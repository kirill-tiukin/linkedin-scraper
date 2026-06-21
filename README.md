# LinkedIn Outreach Scraper

A web app that finds LinkedIn profiles by role and company, enriches them with professional emails via FinalScout, and exports to CSV.

## Features

- Search LinkedIn directly (headless browser with your session)
- DuckDuckGo supplements results if LinkedIn doesn't fill the quota
- **Max results per company** — you control how many per company
- Multiple roles split evenly across the per-company budget
- UK location filter (rejects non-UK profiles)
- FinalScout email enrichment (optional API key)
- Results persist on page refresh
- CSV export
- Real-time streaming results via SSE

## Setup

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure environment

Copy the example and fill in your values:

```bash
cp .env.example .env
```

`.env` variables:
```
# Optional — not required for the app to run
FLASK_DEBUG=0
```

### 3. Run

```bash
python3 app.py
```

Open [http://localhost:5050](http://localhost:5050)

### 4. Connect LinkedIn

Click **Connect** in the sidebar. A browser window will open — log in to LinkedIn. The window closes automatically once login is detected.

### 5. Search

- Enter target roles (one per line)
- Enter companies (one per line)
- Set **Max results per company**
- Optionally add your [FinalScout API key](https://finalscout.com/app/api/settings) for email enrichment
- Click **Start search**

## How results are allocated

| Setting | Result |
|---------|--------|
| Max results = 10, 2 companies, 5 roles | 2 per role per company → up to 10 per company → up to 20 total |
| Max results = 50, 4 companies, 2 roles | 25 per role per company → up to 50 per company → up to 200 total |

LinkedIn runs first (trusted source). DuckDuckGo supplements any slots LinkedIn didn't fill.

## Email enrichment

Add your [FinalScout API key](https://finalscout.com/app/api/settings) in the sidebar. Emails are looked up in parallel after profiles are found. Credits are consumed per email found.

## Requirements

- Python 3.10+
- Chromium (installed via `playwright install chromium`)
- A LinkedIn account
- (Optional) FinalScout API key for email lookup
