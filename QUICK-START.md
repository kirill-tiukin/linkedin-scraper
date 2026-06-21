# LinkedIn Outreach Tool — Quick Start

## First Time Only (run once)

### Mac
Open Terminal, paste this and press Enter:
```
cd ~/Desktop/linkedin-scraper-main && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && playwright install chromium
```

### Windows
Open Command Prompt, paste this and press Enter:
```
cd %USERPROFILE%\Desktop\linkedin-scraper-main && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt && playwright install chromium
```

---

## Every Time You Use It

### Mac
```
cd ~/Desktop/linkedin-scraper-main && source .venv/bin/activate && python3 app.py
```

### Windows
```
cd %USERPROFILE%\Desktop\linkedin-scraper-main && .venv\Scripts\activate && python app.py
```

Then open your browser and go to: **http://localhost:5050**

---

> Make sure the `linkedin-scraper-main` folder is on your Desktop.
> If it's somewhere else, move it there first.
