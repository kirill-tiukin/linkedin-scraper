# LinkedIn Outreach Tool — Setup Guide

---

## Before You Start

This guide has two sections — one for **Mac** and one for **Windows**.
Find your section and follow every step in order.
Each step has a command you copy and paste — you never need to type anything manually.

---

---

# MAC SETUP

---

## Step 1 — Open Terminal

1. Press **Cmd + Space** on your keyboard
2. Type **Terminal**
3. Press **Enter**

A window with a black or white background opens. This is Terminal. **Do not close it** — you will use it throughout this guide.

---

## Step 2 — Check if Python is installed

Click inside the Terminal window, paste the command below, and press **Enter**:

```
python3 --version
```

**What you'll see:**

- If it shows `Python 3.10.x` or higher → **skip to Step 3**
- If it shows `Python 3.9` or lower, or shows an error → follow Step 2a below

### Step 2a — Install Python (only if needed)

Paste this and press **Enter**:

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

⚠️ **Important:** At some point it will say `Password:` and stop. This is asking for your **Mac login password** — the same password you use to unlock your laptop. Type it and press Enter. **You will not see any letters appearing as you type — that is normal.** Just type your password and press Enter.

Wait until you see a `$` symbol appear and it stops scrolling. Then paste this and press Enter:

```
brew install python3
```

Wait for it to finish. Then close Terminal and open it again (Step 1).

---

## Step 3 — Download and install the tool

Paste this entire line and press **Enter**:

```
git clone https://github.com/kirill-tiukin/linkedin-scraper ~/Desktop/linkedin-scraper && cd ~/Desktop/linkedin-scraper && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && playwright install chromium
```

This will take **3–5 minutes**. You will see a lot of text scrolling — that is normal. Do not close Terminal.

When it is done, the scrolling stops and you see a `$` symbol.

---

## Step 4 — Start the tool

Paste this and press **Enter**:

```
cd ~/Desktop/linkedin-scraper && source .venv/bin/activate && python3 app.py
```

You will see something like:
```
* Running on http://127.0.0.1:5050
```

**Do not close Terminal.** The tool runs inside it. If you close Terminal, the tool stops.

---

## Step 5 — Open the tool in your browser

Open **Chrome**, **Safari**, or any browser.

Go to this address: **http://localhost:5050**

You should see the LinkedIn Outreach tool. Setup is complete.

**→ Skip to Part 2 (Using the Tool)**

---

---

# WINDOWS SETUP

---

## Step 1 — Open Command Prompt

1. Press the **Windows key** on your keyboard
2. Type **cmd**
3. Press **Enter**

A black window opens. This is Command Prompt. **Do not close it** — you will use it throughout this guide.

---

## Step 2 — Install Python

Paste this and press **Enter**:

```
winget install Python.Python.3.12
```

Wait for it to finish. When done, you will see `Successfully installed`.

⚠️ **Important:** Close Command Prompt completely and open it again (Step 1) before continuing.

---

## Step 3 — Install Git

Paste this and press **Enter**:

```
winget install Git.Git
```

Wait for it to finish.

⚠️ **Important:** Close Command Prompt completely and open it again (Step 1) before continuing.

---

## Step 4 — Download and install the tool

Paste this entire line and press **Enter**:

```
git clone https://github.com/kirill-tiukin/linkedin-scraper %USERPROFILE%\Desktop\linkedin-scraper && cd %USERPROFILE%\Desktop\linkedin-scraper && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt && playwright install chromium
```

This will take **3–5 minutes**. You will see a lot of text scrolling — that is normal. Do not close Command Prompt.

When it is done, the scrolling stops and you see a `>` symbol.

---

## Step 5 — Start the tool

Paste this and press **Enter**:

```
cd %USERPROFILE%\Desktop\linkedin-scraper && .venv\Scripts\activate && python app.py
```

You will see something like:
```
* Running on http://127.0.0.1:5050
```

**Do not close Command Prompt.** The tool runs inside it. If you close it, the tool stops.

---

## Step 6 — Open the tool in your browser

Open **Chrome**, **Edge**, or any browser.

Go to this address: **http://localhost:5050**

You should see the LinkedIn Outreach tool. Setup is complete.

---

---

# PART 2 — Every Time You Use the Tool

You only need to do this from now on — no more installation steps.

### Mac

1. Open Terminal
2. Paste this and press Enter:
```
cd ~/Desktop/linkedin-scraper && source .venv/bin/activate && python3 app.py
```
3. Open your browser and go to **http://localhost:5050**

### Windows

1. Open Command Prompt
2. Paste this and press Enter:
```
cd %USERPROFILE%\Desktop\linkedin-scraper && .venv\Scripts\activate && python app.py
```
3. Open your browser and go to **http://localhost:5050**

⚠️ **Reminder:** Keep Terminal / Command Prompt open the whole time you use the tool. Minimise it — do not close it.

---

---

# PART 3 — Setting Up Email Finding (FinalScout)

FinalScout finds professional email addresses for the people you search.

**New accounts get 50 free credits.** Each credit = one email found.
If no email is found for someone, no credit is used.

### Step 1 — Create a free account

Go to **https://finalscout.com** and sign up.

### Step 2 — Get your API key

After signing in, go to:
**https://finalscout.com/app/api/settings**

You will see a long code that looks like this:
`3a2458d9a8d4253536d5869790151b91`

Click the copy button next to it, or select it all and press **Ctrl+C** (Windows) or **Cmd+C** (Mac).

### Step 3 — Add it to the tool

In the tool at **http://localhost:5050**, find the **"FinalScout API key"** field in the left sidebar and paste your key there.

Done — every search will now find emails automatically.

**Need more credits?** Go to **https://finalscout.com/app/billing**

---

---

# PART 4 — How to Use the Tool

### Connect your LinkedIn account (once per session)

1. Click **"Connect"** in the left sidebar
2. A browser window opens — log in to your LinkedIn account as normal
3. The window closes on its own once you are logged in
4. You will see **"Session active ●"** — you are ready

### Run a search

Fill in the fields on the left:

- **Target roles** — job titles you want to find, one per line
  Example:
  ```
  HR Manager
  Talent Acquisition
  Head of HR
  ```

- **Companies** — company names, one per line
  Example:
  ```
  BlackRock
  HSBC
  Goldman Sachs
  ```

- **Location** — already set to United Kingdom. Change if needed.

- **Max results per company** — how many people to find at each company.
  If you put `10` and have 2 companies, you get up to 20 people total.

- **FinalScout API key** — paste your key here

Click **"Start search"**. Results appear as they are found.

### Download your results

Click **"↓ Download CSV"** when the search finishes.
Open the file in Excel or Google Sheets.

### Run another search

Click **"↺ New Search"** to clear the results and start fresh.

---

---

# PART 5 — Understanding Your Results

| Column | What it means |
|--------|--------------|
| Name | Person's full name |
| Title | Their current job title |
| Company | Company they work at |
| Location | Where they're based |
| Email | Professional email address |
| Via | Where the result came from (LI = LinkedIn, DDG = DuckDuckGo) |
| ↗ | Click to open their LinkedIn profile |

---

---

# PART 6 — If Something Goes Wrong

**"Session expired" or "Not connected"**
Click **"Reconnect"** in the sidebar and log in to LinkedIn again.

**0 results found**
- Make sure the company name is spelled exactly as it appears on LinkedIn
- Try a shorter role name — "HR" instead of "Senior HR Business Partner"

**No emails appearing**
- Check your credits at **https://finalscout.com/app/billing**
- Some profiles simply do not have a findable email — this is normal

**The website stopped working**
You probably closed Terminal or Command Prompt. Open it again and run the start command from Part 2.

**"command not found" error on Mac after installing Python**
Close Terminal completely, open it again, and try the command again.

**winget is not recognised on Windows**
Your Windows may need an update. Go to the Microsoft Store, search for **"App Installer"** and update it, then try again.

---

*If you are stuck, take a screenshot of the error and send it over.*
