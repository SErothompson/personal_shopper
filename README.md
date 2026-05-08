# Personal Shopper Assistant

Python web app that asynchronously searches supported retailer APIs by product name/description, shows image/description/price results, and supports a daily "Keep Watch" price polling workflow with a time-series chart.

## What This MVP Includes

- FastAPI web app with server-rendered templates
- Async provider fan-out search with partial-result handling
- Result tiles linking to an in-app item details page
- Keep Watch toggle for each item
- Daily polling pipeline (Celery + Redis) for watched items
- Price history chart with 30/90/365 day views
- MIT license

## Compliance and Provider Policy

This project is configured to use official APIs/feeds only.

### Provider status

- eBay: Supported when `EBAY_APP_ID` is configured
- Best Buy: Supported when `BESTBUY_API_KEY` is configured
- Amazon: Coming soon
- JCPenney: Coming soon
- Kohl's: Coming soon
- Walmart: Coming soon
- Target: Coming soon
- Macy's: Coming soon
- Newegg: Coming soon
- TigerDirect: Coming soon

## Tech Stack

- Backend: FastAPI
- Async HTTP: httpx
- Database: SQLite (SQLAlchemy async)
- Scheduler/Workers: Celery + Redis
- Templates: Jinja2
- Charting: Chart.js

## Project Structure

```text
app/
  main.py
  config.py
  database.py
  models.py
  schemas.py
  routers/
    pages.py
  providers/
    base.py
    ebay.py
    bestbuy.py
    coming_soon.py
    registry.py
  services/
    search_orchestrator.py
    pricing.py
    store.py
  tasks/
    celery_app.py
    poll_prices.py
  templates/
    base.html
    index.html
    item_detail.html
  static/
    css/styles.css
    js/app.js
scripts/
  init_db.py
tests/
```

## Setup (Windows PowerShell)

1. Create virtual environment

```powershell
python -m venv .venv
```

2. Activate virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies

```powershell
pip install -r requirements-dev.txt
```

4. Create environment file

```powershell
Copy-Item .env.example .env
```

5. (Optional) Add provider credentials in `.env`

- `EBAY_APP_ID=`
- `BESTBUY_API_KEY=`

6. Initialize database

```powershell
python -m scripts.init_db
```

## Run the Web App

```powershell
uvicorn app.main:app --reload
```

Open: http://127.0.0.1:8000

## Run Keep Watch Polling

Requires Redis running locally on `redis://localhost:6379/0` (default).

Start worker:

```powershell
celery -A app.tasks.celery_app:celery_app worker --loglevel=info --pool=solo
```

Start scheduler (daily 8:00 AM local timezone from `.env`):

```powershell
celery -A app.tasks.celery_app:celery_app beat --loglevel=info
```

## Tests

```powershell
pytest
```

## GitHub Repository (SErothompson)

After authenticating GitHub CLI:

```powershell
git init
git add .
git commit -m "Initial personal shopper MVP scaffold"
gh repo create SErothompson/personal_shopper --public --source . --remote origin --push
```

## Notes

- With no API credentials configured, search results may be empty while provider cards still display readiness/coming-soon status.
- Keep Watch stores snapshots only for items you explicitly enable.
- For production use, swap SQLite for Postgres and run Celery worker/beat as managed services.
