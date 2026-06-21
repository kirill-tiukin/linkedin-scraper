# LinkedIn Outreach Tool — Complete Setup & User Guide

**For people who have never opened a terminal before.**
This guide walks you through everything — installing the tool, setting up email finding, and running your first search. Follow each step in order.

---

## What This Tool Does

This tool finds LinkedIn profiles of people matching a job title at specific companies. It shows you their name, job title, location, and — if you have a FinalScout account — their professional email address. You can then export everything to a spreadsheet (CSV).

**Example:** Search for "HR Manager" at "BlackRock" and "HSBC" → get a list of 10 people per company with emails, ready to export.

---

## Part 1 — One-Time Setup

You only need to do this once. After that, you just run one command each time.

---

### Step 1 — Install Python

Python is the engine that runs the tool. You need version 3.10 or higher.

#### On Mac

1. Open **Terminal**
   - Press `Cmd + Space`, type `Terminal`, press Enter
2. Type this and press Enter:
   ```
   python3 --version
   ```
3. If you see `Python 3.10` or higher — you already have it. Skip to Step 2.
4. If you see an error or a lower version, go to **python.org/downloads**, click the big yellow "Download Python" button, open the downloaded file, and click through the installer.
5. After installing, close Terminal and open it again. Type `python3 --version` to confirm.

#### On Windows

1. Open **Command Prompt**
   - Press the Windows key, type `cmd`, press Enter
2. Type this and press Enter:
   ```
   python --version
   ```
3. If you see `Python 3.10` or higher — skip to Step 2.
4. If not: go to **python.org/downloads**, click "Download Python", open the installer.
   - **Important:** On the first screen of the installer, tick the box that says **"Add Python to PATH"** before clicking Install.
5. After installing, close and reopen Command Prompt. Type `python --version` to confirm.

---

### Step 2 — Download the Tool

1. Go to: **https://github.com/kirill-tiukin/linkedin-scraper**
2. Click the green **"Code"** button
3. Click **"Download ZIP"**
4. Find the downloaded ZIP file (usually in your Downloads folder)
5. **Unzip it:**
   - **Mac:** Double-click the ZIP file
   - **Windows:** Right-click → Extract All → Extract
6. You now have a folder called `linkedin-scraper-main`. Move it somewhere easy to find, like your Desktop.

---

### Step 3 — Run the Setup Script

This installs everything the tool needs. You only do this once.

#### On Mac

1. Open **Terminal**
2. Type `cd ` (with a space after it — don't press Enter yet)
3. Drag the `linkedin-scraper-main` folder from your Desktop into the Terminal window. The path fills in automatically.
4. Press **Enter**
5. Now type this and press Enter:
   ```
   python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && playwright install chromium
   ```
6. Wait — this takes 2–5 minutes. You'll see a lot of text scrolling. That's normal.
7. When it finishes and you see a `$` prompt again, setup is complete.

#### On Windows

1. Open **Command Prompt**
2. Type `cd ` (with a space — don't press Enter yet)
3. Open File Explorer, navigate to the `linkedin-scraper-main` folder, click the address bar at the top, copy the path
4. Paste it into Command Prompt after `cd ` and press **Enter**
5. Now type this and press Enter:
   ```
   python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt && playwright install chromium
   ```
6. Wait 2–5 minutes for everything to install.

---

## Part 2 — Every Time You Use It

### Step 4 — Start the Tool

#### On Mac

1. Open **Terminal**
2. Navigate to the folder (same as Step 3 above — `cd` then drag the folder)
3. Type this and press Enter:
   ```
   source .venv/bin/activate && python3 app.py
   ```

#### On Windows

1. Open **Command Prompt**
2. Navigate to the folder
3. Type this and press Enter:
   ```
   .venv\Scripts\activate && python app.py
   ```

4. Open your web browser (Chrome, Safari, Edge — any)
5. Go to: **http://localhost:5050**

You should see the LinkedIn Outreach tool. Leave the Terminal/Command Prompt window open while you use it — closing it stops the tool.

---

## Part 3 — Setting Up FinalScout (for Email Finding)

FinalScout finds professional email addresses for the profiles you scrape. New accounts get **50 free credits**. Each credit finds one email.

### What you get with 50 credits

| Credits used | Emails found |
|-------------|-------------|
| 10 | Up to 10 emails |
| 50 | Up to 50 emails |

FinalScout only uses a credit when it actually finds an email — if no email is found, no credit is spent.

### How to set up FinalScout

1. Go to **https://finalscout.com**
2. Click **"Sign Up"** — create a free account
3. After signing in, go to: **https://finalscout.com/app/api/settings**
4. You'll see your **API Key** — it looks something like: `3a2458d9a8d4253536d5869790151b91`
5. Copy it (click the copy button or select all and Ctrl+C / Cmd+C)
6. In the LinkedIn Outreach tool, paste it into the **"FinalScout API key"** field in the sidebar

That's it. Every search you run will now automatically look up emails.

### Buying more credits

After your 50 free credits, you can buy more at **finalscout.com/app/billing**.
Pricing is roughly $0.10–$0.50 per email depending on the plan.

---

## Part 4 — Using the Tool

### The Sidebar (left panel)

**Target roles** — Enter the job titles you're looking for, one per line.
Examples:
```
HR Manager
Head of HR
Talent Acquisition
People Operations
```

**Companies** — Enter the company names, one per line.
Examples:
```
BlackRock
HSBC
Goldman Sachs
```

**Location** — Where to search. Default is "United Kingdom". You can change this.

**Max results per company** — How many people to find at each company. If you put 10 and have 2 companies, you'll get up to 20 total (10 per company).

**LinkedIn** — Shows whether you're connected. You need to connect once per session.

**FinalScout API key** — Paste your key here to enable email finding.

---

### Step-by-Step: Running a Search

1. **Connect LinkedIn** (first time each session)
   - Click the **"Connect"** button in the sidebar
   - A Chromium browser window opens — log in to your LinkedIn account
   - Once logged in, the window closes automatically
   - The status changes to "Session active ●"

2. **Fill in your search**
   - Enter roles (one per line)
   - Enter companies (one per line)
   - Set how many results per company
   - Paste your FinalScout API key (optional but recommended)

3. **Click "Start search"**
   - Results appear in real time as they're found
   - The status bar at the bottom of the sidebar shows progress
   - Company pills at the top show which companies are done

4. **Download your results**
   - Click **"↓ Download CSV"** when the search finishes
   - Open the CSV in Excel or Google Sheets

5. **Run a new search**
   - Click **"↺ New Search"** to clear results and start fresh
   - Your previous results are saved until you click this

---

### Understanding Your Results

| Column | What it means |
|--------|--------------|
| Name | Person's full name |
| Title | Their current job title |
| Company | Company they work at |
| Location | Where they're based |
| Email | Professional email (if FinalScout found one) |
| Via | Where the result came from: LI = LinkedIn, DDG = DuckDuckGo |
| ↗ | Link to their LinkedIn profile |

---

## Part 5 — Tips & Troubleshooting

### Getting better results

- **Be specific with roles.** "HR Manager" finds more than "Human Resources".
- **One company at a time** if you want to check results before continuing.
- **Start with 5–10 results** per company to test before going to 50.
- **UK results only** — the tool filters non-UK profiles automatically.

### FinalScout is not finding emails

- Check your credit balance at **finalscout.com/app/billing**
- Some profiles simply don't have a findable email — that's normal
- FinalScout works best for people with a clear professional presence

### "Session expired" error

Your LinkedIn session timed out. Click **"Reconnect"** and log in again.

### The tool finds 0 results

- Check that your company name is spelled exactly as it appears on LinkedIn
- Try a broader role name ("HR" instead of "Senior HR Business Partner")
- Make sure your LinkedIn session is active (green dot)

### Closing and reopening the tool

When you close Terminal/Command Prompt, the tool stops. Next time:
1. Open Terminal / Command Prompt
2. Navigate to the folder
3. Run the start command from Step 4
4. Your previous results will still be there in the browser

### The browser window doesn't open when I click Connect

Make sure you ran the start command first and the terminal window is still open.

---

## Quick Reference Card

| Task | Mac command | Windows command |
|------|------------|----------------|
| Start the tool | `source .venv/bin/activate && python3 app.py` | `.venv\Scripts\activate && python app.py` |
| Open in browser | Go to http://localhost:5050 | Go to http://localhost:5050 |

**FinalScout:** https://finalscout.com · API key at https://finalscout.com/app/api/settings

**Tool source:** https://github.com/kirill-tiukin/linkedin-scraper

---

*If something isn't working, take a screenshot of the error and share it.*
