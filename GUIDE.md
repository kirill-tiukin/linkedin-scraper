# LinkedIn Outreach Tool — Setup & User Guide

---

## Part 1 — Setup (One Time Only)

---

### On Mac

**Step 1 — Open Terminal**

Press `Cmd + Space`, type **Terminal**, press Enter.

---

**Step 2 — Install Python**

Paste this and press Enter:

```
python3 --version
```

If you see `Python 3.10` or higher — skip to Step 3.

If you see an error, paste this and press Enter (installs Python automatically):

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" && brew install python3
```

This takes a few minutes. When it finishes, close Terminal and open it again.

---

**Step 3 — Download and set up the tool**

Paste this entire block and press Enter:

```
git clone https://github.com/kirill-tiukin/linkedin-scraper ~/Desktop/linkedin-scraper && cd ~/Desktop/linkedin-scraper && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && playwright install chromium
```

This takes 2–5 minutes. Wait until you see the `$` prompt again.

---

**Step 4 — Start the tool**

Paste this and press Enter:

```
cd ~/Desktop/linkedin-scraper && source .venv/bin/activate && python3 app.py
```

Then open your browser and go to: **http://localhost:5050**

The tool is running. Keep Terminal open while you use it.

---

### On Windows

**Step 1 — Open Command Prompt**

Press the Windows key, type **cmd**, press Enter.

---

**Step 2 — Install Python**

Paste this and press Enter:

```
winget install Python.Python.3.12
```

When it finishes, close Command Prompt and open it again.

---

**Step 3 — Install Git**

Paste this and press Enter:

```
winget install Git.Git
```

When it finishes, close Command Prompt and open it again.

---

**Step 4 — Download and set up the tool**

Paste this entire block and press Enter:

```
git clone https://github.com/kirill-tiukin/linkedin-scraper %USERPROFILE%\Desktop\linkedin-scraper && cd %USERPROFILE%\Desktop\linkedin-scraper && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt && playwright install chromium
```

This takes 2–5 minutes. Wait until you see a prompt again.

---

**Step 5 — Start the tool**

Paste this and press Enter:

```
cd %USERPROFILE%\Desktop\linkedin-scraper && .venv\Scripts\activate && python app.py
```

Then open your browser and go to: **http://localhost:5050**

The tool is running. Keep Command Prompt open while you use it.

---

## Part 2 — Every Time You Use It

You only need to paste one command and open your browser.

**Mac:**
```
cd ~/Desktop/linkedin-scraper && source .venv/bin/activate && python3 app.py
```

**Windows:**
```
cd %USERPROFILE%\Desktop\linkedin-scraper && .venv\Scripts\activate && python app.py
```

Then go to: **http://localhost:5050**

---

## Part 3 — Setting Up FinalScout (Email Finding)

FinalScout finds professional email addresses for the people you search. New accounts get **50 free credits** — each credit finds one email. No credit is used if no email is found.

**Step 1 — Create a free account**

Go to **https://finalscout.com** and sign up.

**Step 2 — Get your API key**

After signing in, go to: **https://finalscout.com/app/api/settings**

Copy the API key shown on that page. It looks like: `3a2458d9a8d4253536d5869790151b91`

**Step 3 — Paste it into the tool**

In the tool sidebar, find the **"FinalScout API key"** field and paste your key there.

That's it — every search will now automatically look up emails.

**Running out of credits?** Buy more at **https://finalscout.com/app/billing**

---

## Part 4 — Using the Tool

### First time each session: Connect LinkedIn

1. Click **"Connect"** in the sidebar
2. A browser window opens — log in to your LinkedIn account
3. Once logged in, the window closes automatically
4. You'll see **"Session active ●"** — you're ready

### Run a search

Fill in the sidebar:

- **Target roles** — job titles you want to find, one per line (e.g. HR Manager)
- **Companies** — company names, one per line (e.g. BlackRock)
- **Location** — defaults to United Kingdom
- **Max results per company** — how many people per company (e.g. 10)
- **FinalScout API key** — paste your key here for emails

Click **"Start search"** — results appear in real time.

### Download results

Click **"↓ Download CSV"** when done. Open it in Excel or Google Sheets.

### Start a new search

Click **"↺ New Search"** to clear the results and search again.

---

## Part 5 — Understanding Your Results

| Column | What it means |
|--------|--------------|
| Name | Person's full name |
| Title | Their current job title |
| Company | Company they work at |
| Location | Where they're based |
| Email | Professional email (if FinalScout found one) |
| Via | LI = found on LinkedIn, DDG = found on DuckDuckGo |
| ↗ | Link to their LinkedIn profile |

---

## Part 6 — Troubleshooting

**"Session expired" or "Not connected"**
Click **"Reconnect"** and log in to LinkedIn again.

**0 results found**
- Check the company name is spelled exactly as it appears on LinkedIn
- Try a simpler role name ("HR" instead of "Senior HR Business Partner")

**No emails showing**
- Check your FinalScout credits at **https://finalscout.com/app/billing**
- Some profiles simply don't have a findable email — that's normal

**Tool stopped working**
Close Terminal/Command Prompt and run the start command again.

---

## Quick Reference

| | Mac | Windows |
|--|-----|---------|
| **Start the tool** | `cd ~/Desktop/linkedin-scraper && source .venv/bin/activate && python3 app.py` | `cd %USERPROFILE%\Desktop\linkedin-scraper && .venv\Scripts\activate && python app.py` |
| **Open in browser** | http://localhost:5050 | http://localhost:5050 |

**FinalScout API key:** https://finalscout.com/app/api/settings

**Tool download (if needed):** https://github.com/kirill-tiukin/linkedin-scraper
