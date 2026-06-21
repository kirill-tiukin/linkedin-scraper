"""
LinkedIn people search — extracts profile data from search results without
visiting individual profile pages (avoids rate limiting).

LinkedIn ignores the ?start= URL parameter in headless mode. Pagination
requires clicking the numbered page buttons (aria-label="Page N").
"""
import asyncio
import logging
import re
from urllib.parse import urlencode

from playwright.async_api import Page

logger = logging.getLogger(__name__)

_BASE = "https://www.linkedin.com/search/results/people/"
_PAGE_SIZE = 10  # LinkedIn shows exactly 10 results per page


def build_search_url(role: str, company: str, location: str = "") -> str:
    params: dict = {"keywords": role, "origin": "FACETED_SEARCH"}
    if company:
        params["company"] = company
    if location:
        params["geoUrn"] = '["101165590"]'   # LinkedIn URN for United Kingdom
    return f"{_BASE}?{urlencode(params)}"


def _clean(text: str) -> str:
    text = re.sub(r"[•·].*?(1st|2nd|3rd)\s*", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_card_text(raw: str) -> tuple[str, str, str]:
    sections = [s.strip() for s in re.split(r"\n{2,}", raw) if s.strip()]
    name = _clean(sections[0].split("\n")[0]) if sections else ""
    title = _clean(sections[1]) if len(sections) > 1 else ""
    location = _clean(sections[2]) if len(sections) > 2 else ""
    return name, title, location


async def extract_profiles_from_page(page: Page) -> list[dict]:
    """Extract all profile cards from the current search results page."""
    await page.wait_for_load_state("domcontentloaded")
    await asyncio.sleep(2)

    for _ in range(4):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(0.8)

    raw_links: list[dict] = await page.evaluate(r"""
    () => {
        const seen = new Set();
        const results = [];
        const links = document.querySelectorAll('a[href*="/in/"]');
        for (const a of links) {
            const href = a.href.split('?')[0].replace(/\/$/, '');
            if (!href.includes('/in/') || seen.has(href)) continue;
            const text = a.innerText || '';
            if (!text.includes('\n')) continue;
            seen.add(href);
            results.push({ href, text });
        }
        return results;
    }
    """)

    profiles: list[dict] = []
    for item in raw_links:
        href = item["href"]
        if not re.search(r"linkedin\.com/in/[^/]+$", href):
            continue
        name, title, location = _parse_card_text(item["text"])
        if not name:
            continue
        profiles.append({"url": href, "name": name, "title": title, "location": location})

    logger.info("  Page extracted %d profiles", len(profiles))
    return profiles


async def _click_page(page: Page, page_num: int) -> bool:
    """
    Click the numbered page button (aria-label='Page N').
    Returns True if the click succeeded, False if button not found.
    """
    btn = page.locator(f'button[aria-label="Page {page_num}"]')
    if await btn.count() == 0:
        # Fallback: button with text matching the page number
        btn = page.locator(f'button:has-text("{page_num}")').first
        if await btn.count() == 0:
            logger.info("  No page %d button found", page_num)
            return False
    try:
        await btn.scroll_into_view_if_needed()
        await btn.click()
        await asyncio.sleep(2)
        await page.wait_for_load_state("domcontentloaded")
        return True
    except Exception as e:
        logger.warning("  Page %d button click failed: %s", page_num, e)
        return False


def _is_stopped(stop_flag) -> bool:
    if stop_flag is None:
        return False
    if isinstance(stop_flag, dict):
        return bool(stop_flag.get("stop"))
    return bool(stop_flag[0])


async def search_people(
    page: Page,
    company: str,
    roles: list[str],
    location: str = "United Kingdom",
    limit_per_role: int = 5,
    stop_flag=None,
):
    """
    Async generator — yields (profile_dict, role, company) triples.
    Paginates via page-number button clicks (LinkedIn ignores ?start= in headless mode).
    """
    seen_urls: set[str] = set()

    for role in roles:
        if _is_stopped(stop_flag):
            return

        url = build_search_url(role, company, location)
        logger.info("LinkedIn search [%s @ %s]: %s", role, company, url)

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        except Exception as e:
            logger.warning("Navigation failed [%s @ %s]: %s", role, company, e)
            continue

        if any(x in page.url for x in ("login", "authwall", "checkpoint")):
            logger.error("Auth wall hit — session expired")
            return

        collected = 0
        current_page = 1

        while collected < limit_per_role:
            if _is_stopped(stop_flag):
                return

            profiles = await extract_profiles_from_page(page)
            logger.info("  Page %d: %d profiles, need %d more",
                        current_page, len(profiles), limit_per_role - collected)

            if not profiles:
                break

            new_on_page = 0
            for p in profiles:
                if collected >= limit_per_role:
                    break
                if _is_stopped(stop_flag):
                    return
                if p["url"] in seen_urls:
                    continue
                seen_urls.add(p["url"])
                collected += 1
                new_on_page += 1
                yield p, role, company

            # No new profiles on this page or didn't fill a full page → done
            if new_on_page == 0 or len(profiles) < _PAGE_SIZE:
                break

            if collected >= limit_per_role:
                break

            # Navigate to next page via button click
            next_page = current_page + 1
            clicked = await _click_page(page, next_page)
            if not clicked:
                logger.info("  Cannot navigate to page %d — stopping", next_page)
                break

            current_page = next_page
            await asyncio.sleep(2)

        await asyncio.sleep(2)
