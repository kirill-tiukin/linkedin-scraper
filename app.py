import asyncio
import csv
import io
import json
import logging
import os
import queue
import re
import threading
import time
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request, stream_with_context

from people_search import search_people

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

SESSION_FILE = Path(__file__).parent / "linkedin_session.json"

# job_id → {status, results, queue, stop, created_at}
_jobs: dict[str, dict] = {}
_JOB_TTL = 3600  # evict jobs older than 1 hour


def _get_job(job_id: str) -> dict | None:
    return _jobs.get(job_id)


def _evict_old_jobs() -> None:
    cutoff = time.time() - _JOB_TTL
    stale = [k for k, v in _jobs.items() if v.get("created_at", 0) < cutoff]
    for k in stale:
        _jobs.pop(k, None)


# ── helpers ───────────────────────────────────────────────────────────────────

def _normalise_url(url: str) -> str:
    url = url.split("?")[0].rstrip("/")
    return re.sub(r"https?://[a-z-]+\.linkedin\.com/", "https://www.linkedin.com/", url)


def _normalise_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.lower().strip())


_UK_TERMS = {
    "uk", "united kingdom", "england", "scotland", "wales", "northern ireland",
    "london", "manchester", "birmingham", "leeds", "glasgow", "edinburgh",
    "bristol", "liverpool", "sheffield", "newcastle", "nottingham",
    "cambridge", "oxford", "bath", "reading", "cardiff", "belfast",
    "brighton", "southampton", "coventry", "leicester",
}

_NON_UK_TERMS = {
    "united states", "usa", "u.s.a", "new york", "san francisco", "california",
    "texas", "chicago", "boston", "seattle", "toronto", "canada", "australia",
    "sydney", "melbourne", "india", "singapore", "hong kong", "germany",
    "france", "netherlands", "dubai", "uae", "new zealand",
}


def _is_uk(location: str) -> bool:
    """
    Returns True if location is UK or unknown (empty).
    Returns False if location is explicitly non-UK.
    DDG profiles with no parseable location are kept (assume UK since query is UK-targeted).
    """
    if not location:
        return True
    loc_lower = location.lower()
    # Explicit non-UK location → reject
    if any(term in loc_lower for term in _NON_UK_TERMS):
        return False
    # Explicit UK location → accept
    if any(term in loc_lower for term in _UK_TERMS):
        return True
    # Ambiguous: keep it (don't discard on uncertainty)
    return True


def _sanitise_url(url: str) -> str:
    """Strip javascript: and data: scheme URLs to prevent XSS via href."""
    if re.match(r"^\s*(javascript|data|vbscript):", url, re.I):
        return "#"
    return url


# ── FinalScout email lookup ───────────────────────────────────────────────────
# Max 2 concurrent FinalScout requests — more causes SSLEOFError
_finalscout_sem = threading.Semaphore(2)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_valid_email(value: str) -> bool:
    return bool(value and _EMAIL_RE.match(value.strip()))


def _find_email(linkedin_url: str, api_key: str) -> str:
    if not api_key:
        return ""

    if not linkedin_url.startswith("http"):
        linkedin_url = "https://www." + linkedin_url.lstrip("/")

    # Per official API spec: Authorization = raw key (no Bearer),
    # body = {"person": {"linkedin_url": "..."}}
    # Waterfall endpoint keeps connection open until done (long-poll).
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    body = {
        "person": {"linkedin_url": linkedin_url},
        "enable_work_email": True,
        "enable_personal_email": True,
    }

    with _finalscout_sem:
        for attempt in range(3):
            try:
                if attempt > 0:
                    time.sleep(2 * attempt)  # back off before retry

                resp = requests.post(
                    "https://api-waterfall.finalscout.com/find/linkedin/single?timeout=120",
                    json=body,
                    headers=headers,
                    timeout=130,
                )
                logger.info("FinalScout [%s] attempt %d → HTTP %d: %s",
                            linkedin_url, attempt + 1, resp.status_code, resp.text[:400])

                if resp.status_code == 408:
                    continue

                if resp.status_code == 403:
                    logger.warning("FinalScout 403 — API key invalid or credits exhausted")
                    return "NO_CREDITS"

                if resp.status_code != 200:
                    return ""

                data = resp.json()
                contact = data.get("contact") or {}
                email = contact.get("email", "")
                if _is_valid_email(email):
                    logger.info("FinalScout found email for %s: %s", linkedin_url, email)
                    return email
                return ""

            except Exception as e:
                logger.warning("FinalScout error for %s (attempt %d): %s", linkedin_url, attempt + 1, e)

    return ""


# ── DuckDuckGo search ─────────────────────────────────────────────────────────

def _ddg_search(role: str, company: str, location: str, n: int) -> list[dict]:
    """
    Query DuckDuckGo for LinkedIn profiles matching role+company+location.
    Parses name/title from DDG result titles without visiting individual profiles.
    """
    try:
        from ddgs import DDGS
    except ImportError:
        logger.warning("ddgs not installed — skipping DuckDuckGo search")
        return []

    # Include location in query so DDG pre-filters geographically
    query = f'site:linkedin.com/in "{role}" "{company}"'
    if location:
        query += f" {location}"

    # Fetch 4× requested — after UK filter + dedup against LinkedIn results we need headroom
    fetch_count = max(n * 4, 40)
    try:
        with DDGS() as ddgs:
            hits = list(ddgs.text(query, max_results=fetch_count))
        logger.info("DDG [%s @ %s]: fetched %d raw hits", role, company, len(hits))
    except Exception as e:
        logger.warning("DDG search failed [%s @ %s]: %s", role, company, e)
        return []

    results: list[dict] = []
    for hit in hits:
        if len(results) >= n:
            break
        href = hit.get("href", "")
        if "linkedin.com/in/" not in href:
            continue
        url = _normalise_url(href)
        if not re.search(r"linkedin\.com/in/[^/]+$", url):
            continue

        raw_title = hit.get("title", "")
        name, title = _parse_ddg_title(raw_title)
        if not name:
            continue

        body = hit.get("body", "")
        loc = _extract_location_from_snippet(body)

        # Filter out explicitly non-UK profiles at source
        if not _is_uk(loc):
            logger.debug("DDG skipping non-UK profile: %s (%s)", name, loc)
            continue

        results.append({"url": url, "name": name, "title": title, "location": loc})

    return results


def _parse_ddg_title(raw: str) -> tuple[str, str]:
    """Parse 'Name - Title at Company | LinkedIn' → (name, title)."""
    raw = re.sub(r"\s*\|.*$", "", raw).strip()
    raw = re.sub(r"\s*-\s*LinkedIn\s*$", "", raw)
    parts = re.split(r"\s+-\s+", raw, maxsplit=1)
    name = parts[0].strip()
    title = parts[1].strip() if len(parts) > 1 else ""
    title = re.sub(r"\s+at\s+.+$", "", title, flags=re.I).strip()
    return name, title


def _extract_location_from_snippet(body: str) -> str:
    """Extract a location string from a DDG result snippet."""
    m = re.search(
        r"([A-Z][a-zA-Z ]+,\s*(?:England|Scotland|Wales|United Kingdom|Northern Ireland|UK))",
        body,
    )
    if m:
        return m.group(1)
    # Check non-UK patterns to enable rejection even when no structured location found
    body_lower = body.lower()
    for term in _NON_UK_TERMS:
        if term in body_lower:
            return term.title()  # return something non-empty so _is_uk can reject it
    if "united kingdom" in body_lower or re.search(r"\buk\b", body_lower):
        return "United Kingdom"
    return ""


# ── session creation ──────────────────────────────────────────────────────────

async def _async_create_session(q: queue.Queue) -> None:
    from linkedin_scraper import BrowserManager

    def push(event: str, data: dict) -> None:
        q.put({"event": event, "data": data})

    push("status", {"msg": "Opening LinkedIn in a new browser window…"})

    try:
        async with BrowserManager(headless=False) as browser:
            # Try to navigate — if the connection drops, still keep the browser open
            try:
                await browser.page.goto("https://www.linkedin.com/login",
                                        wait_until="domcontentloaded", timeout=20_000)
            except Exception:
                # Navigation failed — browser is still open, user can type the URL manually
                pass

            push("status", {"msg": "Please log in to LinkedIn in the browser window. It will close automatically once detected."})

            # Poll every second for up to 5 minutes until user reaches the feed
            logged_in = False
            for _ in range(300):
                await asyncio.sleep(1)
                try:
                    url = browser.page.url
                except Exception:
                    continue
                if any(x in url for x in ("/feed", "/mynetwork", "/jobs", "/messaging", "/notifications")):
                    logged_in = True
                    break
                if "linkedin.com" in url and not any(x in url for x in ("login", "authwall", "checkpoint", "signup", "about:blank")):
                    logged_in = True
                    break

            if not logged_in:
                push("error", {"msg": "Login timed out (5 min). Please try again."})
                q.put(None)
                return

            push("status", {"msg": "Login detected — saving session…"})
            try:
                await browser.save_session(str(SESSION_FILE))
            except Exception as e:
                push("error", {"msg": f"Failed to save session: {e}"})
                q.put(None)
                return

            if not SESSION_FILE.exists():
                push("error", {"msg": "Session file was not created. Please try again."})
                q.put(None)
                return

            push("done", {"msg": "Session saved — window closing now."})

    except Exception as e:
        logger.exception("Session creation error")
        push("error", {"msg": f"Session creation failed: {e}"})

    q.put(None)


def _run_create_session(q: queue.Queue) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_async_create_session(q))
    except Exception as e:
        q.put({"event": "error", "data": {"msg": str(e)}})
        q.put(None)
    finally:
        loop.close()


# ── scrape job ────────────────────────────────────────────────────────────────

async def _async_scrape(job_id: str, params: dict) -> None:
    from linkedin_scraper import BrowserManager

    job = _jobs[job_id]
    q: queue.Queue = job["queue"]

    def push(event: str, data: dict) -> None:
        q.put({"event": event, "data": data})

    if not SESSION_FILE.exists():
        push("fatal", {"msg": "No LinkedIn session found. Click 'Connect LinkedIn' first."})
        q.put(None)
        return

    companies: list[str] = params["companies"]
    roles: list[str] = params["roles"]
    location: str = params["location"]
    n: int = params["n"]          # max results PER COMPANY (set by user)
    finalscout_key: str = params["finalscout_key"]

    seen_urls: set[str] = set()
    seen_names: set[str] = set()
    total_found = 0
    email_threads: list[threading.Thread] = []

    # Per-company counter — reset each company loop iteration
    company_found = 0

    def _at_company_cap() -> bool:
        return company_found >= n

    def _emit_row(url: str, name: str, title: str, loc: str, company: str, source: str) -> bool:
        nonlocal total_found, company_found
        if _at_company_cap():
            return False

        norm = _normalise_url(_sanitise_url(url))
        if norm in seen_urls:
            return False
        seen_urls.add(norm)

        name = name.strip()
        if not name:
            return False
        nn = _normalise_name(name)
        if nn in seen_names:
            return False
        seen_names.add(nn)

        if not _is_uk(loc):
            logger.debug("Skipping non-UK: %s (%s)", name, loc)
            return False

        row = {
            "name": name,
            "headline": title,
            "location": loc,
            "current_company": company,
            "profile_url": norm,
            "email": "",
            "source": source,
        }
        job["results"].append(row)
        total_found += 1
        company_found += 1
        q.put({"event": "result", "data": row})
        q.put({"event": "status", "data": {"msg": f"Found {name} ({source}) — {company_found}/{n} for {company}"}})

        if finalscout_key:
            def _et(u=norm, k=finalscout_key, r=row):
                result = _find_email(u, k)
                if result == "NO_CREDITS":
                    q.put({"event": "status", "data": {"msg": "⚠️ FinalScout: API key invalid or credits exhausted — emails skipped"}})
                    result = ""
                r["email"] = result
                q.put({"event": "email_update", "data": {"profile_url": u, "email": result}})
            t = threading.Thread(target=_et, daemon=True)
            t.start()
            email_threads.append(t)

        return True

    async with BrowserManager(headless=True) as browser:
        push("status", {"msg": "Loading LinkedIn session…"})
        try:
            await browser.load_session(str(SESSION_FILE))
        except Exception as e:
            push("fatal", {"msg": f"Could not load session: {e}. Try reconnecting."})
            q.put(None)
            return

        push("status", {"msg": "Session loaded — starting search…"})
        ev_loop = asyncio.get_running_loop()

        for company in companies:
            if job["stop"]:
                break

            # Reset per-company counter for each company
            company_found = 0

            push("company_status", {"company": company, "status": "searching"})

            # ── 1. LinkedIn first — split n evenly across roles ──────────────
            per_role = max(1, n // len(roles))
            try:
                async for profile, _role, _co in search_people(
                    page=browser.page,
                    company=company,
                    roles=roles,
                    location=location,
                    limit_per_role=per_role,
                    stop_flag=job,
                ):
                    if job["stop"] or _at_company_cap():
                        break
                    _emit_row(profile["url"], profile.get("name", ""),
                              profile.get("title", ""), profile.get("location", ""),
                              company, "LinkedIn")
            except Exception as li_err:
                logger.warning("LinkedIn search error [%s]: %s", company, li_err)
                push("status", {"msg": f"LinkedIn issue for {company}: {li_err}"})

            # ── 2. DDG supplements if LinkedIn didn't fill this company's quota ──
            if not job["stop"] and not _at_company_cap():
                push("status", {"msg": f"DDG supplementing for {company} ({n - company_found} more needed)…"})
                for role in roles:
                    if job["stop"] or _at_company_cap():
                        break
                    ddg_profiles = await ev_loop.run_in_executor(
                        None, _ddg_search, role, company, location, n - company_found
                    )
                    for p in ddg_profiles:
                        if job["stop"] or _at_company_cap():
                            break
                        _emit_row(p["url"], p["name"], p["title"],
                                  p["location"], company, "DDG")

            push("company_status", {"company": company, "status": "done"})

    # Wait for all FinalScout email lookups to finish before closing the stream
    if email_threads:
        push("status", {"msg": f"Waiting for {len(email_threads)} email lookups…"})
        for t in email_threads:
            t.join(timeout=90)

    job["status"] = "done"
    push("done", {"count": total_found})
    q.put(None)


def _run_job(job_id: str, params: dict) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_async_scrape(job_id, params))
    except BaseException as e:
        logger.exception("Job %s crashed: %s", job_id, e)
        job = _jobs.get(job_id)
        if job:
            msg = f"{type(e).__name__}: {e}" if str(e) in ("", "0") else str(e)[:300]
            job["queue"].put({"event": "fatal", "data": {"msg": msg}})
            job["queue"].put(None)
    finally:
        loop.close()


# ── routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/session-status")
def api_session_status():
    if not SESSION_FILE.exists():
        return jsonify(connected=False)
    try:
        data = json.loads(SESSION_FILE.read_text())
        valid = isinstance(data.get("cookies"), list)
    except Exception:
        valid = False
    return jsonify(connected=valid)


@app.route("/api/connect-linkedin")
def api_connect_linkedin():
    q: queue.Queue = queue.Queue()
    threading.Thread(target=_run_create_session, args=(q,), daemon=True).start()

    def generate():
        while True:
            msg = q.get()
            if msg is None:
                break
            yield f"event: {msg['event']}\ndata: {json.dumps(msg['data'])}\n\n"

    return Response(stream_with_context(generate()),
                    mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/start", methods=["POST"])
def api_start():
    _evict_old_jobs()
    body = request.get_json(silent=True) or {}

    roles = [r.strip() for r in (body.get("positions") or "").splitlines() if r.strip()]
    if not roles:
        return jsonify(error="Enter at least one target role"), 400

    # Cap inputs to prevent runaway scraping
    roles = roles[:20]
    companies = [c.strip() for c in (body.get("companies") or "").splitlines() if c.strip()][:20] or [""]

    params = {
        "roles":          roles,
        "companies":      companies,
        "location":       (body.get("location_filter") or "United Kingdom").strip()[:100],
        "n":              max(1, int(body.get("n") or 10)),
        "finalscout_key": (body.get("finalscout_key") or "").strip(),
    }

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status":     "running",
        "results":    [],
        "queue":      queue.Queue(),
        "stop":       False,
        "created_at": time.time(),
    }
    threading.Thread(target=_run_job, args=(job_id, params), daemon=True).start()
    return jsonify(job_id=job_id)


@app.route("/api/stop/<job_id>", methods=["POST"])
def api_stop(job_id: str):
    job = _get_job(job_id)
    if job:
        job["stop"] = True
    return jsonify(ok=True)


@app.route("/api/stream/<job_id>")
def api_stream(job_id: str):
    job = _get_job(job_id)
    if not job:
        return jsonify(error="not found"), 404

    def generate():
        q: queue.Queue = job["queue"]
        while True:
            msg = q.get()
            if msg is None:
                break
            yield f"event: {msg['event']}\ndata: {json.dumps(msg['data'])}\n\n"

    return Response(stream_with_context(generate()),
                    mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/download/<job_id>")
def api_download(job_id: str):
    job = _get_job(job_id)
    if not job:
        return jsonify(error="not found"), 404

    fields = ["name", "headline", "location", "current_company", "profile_url", "email", "source"]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(job["results"])

    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition":
                             f'attachment; filename="linkedin-contacts-{job_id[:8]}.csv"'})


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug, port=5050, threaded=True)
