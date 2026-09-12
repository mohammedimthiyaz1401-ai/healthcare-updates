# Healthcare Updates India - AGENTS.md

## What
Automated healthcare news aggregator for India. Fetches news every hour, displays by category, 7-day rolling archive.

## Tech Stack
- HTML/JS frontend (single-page, no framework)
- Python 3.11+ (news fetcher)
- feedparser (RSS parsing)
- GitHub Actions (hourly cron)
- Vercel (hosting)

## Key Files
- index.html - Main website (categories, date filter, search)
- scripts/fetch_news.py - Hourly news fetcher
- data/*.json - Today's news only
- data/archive/YYYY-MM-DD/ - 7-day rolling archive
- data/dates.json - Available dates for filter
- .github/workflows/daily_news.yml - Hourly cron (0 * * * *)

## How to Deploy
1. Push to master branch
2. GitHub Actions auto-deploys to GitHub Pages
3. For Vercel: vercel --yes --prod (from local)

## How to Run Locally
```
pip install feedparser requests
cd scripts
python fetch_news.py
```
Then open index.html in browser.

## Categories
Telangana, MCI/NMC, Regulations, Hospitals, Launches, Central Govt, Healthcare Tech (AI/ML, MedTech, Telehealth, Genomics, Robotics, Startups)

## Known Issues (All Fixed)
1. Date filter not working: Fixed with parse_date() normalizing all formats to YYYY-MM-DD
2. Count accumulation: clearInterval() per timer prevents count inflation
3. Custom date shows wrong default: Fixed to show today's date
4. Category tabs show "undefined": Fixed - use t.cat not t.label
5. Fetcher accumulates old data: Fixed - fetch_news.py clears data/*.json daily
6. Event.target bug: Fixed - use e.currentTarget for tab clicks
7. Frontend shows stale data: loadCategoryData() filters by parsed date

## Troubleshooting
- No news showing: Check if data/*.json has today's date files
- Count wrong: Hard refresh (Ctrl+Shift+R), check clearInterval in JS
- Categories missing: Verify MENU array in index.html has cat property

## .gitignore
__pycache__/
*.pyc
