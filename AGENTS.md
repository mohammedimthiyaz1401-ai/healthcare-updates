# Healthcare Updates India — Memory

## Overview
- **Repo:** mohammedimthiyaz1401-ai/healthcare-updates
- **Local:** `C:\Users\Imtiyaz\Documents\healthcare-updates`
- **Vercel:** https://healthcare-updates.vercel.app
- **Auto-updates:** Every hour via GitHub Actions (`0 * * * *`)

## Key Files
- `index.html` — Main website with date filter, 7 categories
- `scripts/fetch_news.py` — Hourly news fetcher
- `data/*.json` — Today's data only
- `data/archive/YYYY-MM-DD/` — 7-day rolling archive
- `data/dates.json` — Available dates for filter

## Categories
Telangana, MCI/NMC, Regulations, Hospitals, Launches, Central Govt, Healthcare Tech (AI/ML, MedTech, Telehealth, Genomics, Robotics, Startups)

## Important Fixes Applied
1. **Date filter:** `parse_date()` normalizes all date formats to YYYY-MM-DD
2. **Count accumulation:** `clearInterval()` per timer prevents count inflation
3. **Custom date:** Shows today's date as default
4. **Category tabs:** Use `t.cat` not `t.label`
5. **Fetch accumulation:** `fetch_news.py` clears old data daily
6. **Event.target bug:** Use `e.currentTarget` for tab clicks
7. **Frontend filtering:** `loadCategoryData()` filters items by parsed date
