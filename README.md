# Brand Sale Tracker MVP

This project is a backend-first MVP for a service that:

- tracks product prices across brands and retailers
- stores up to two years of historical price observations
- estimates when a brand tends to go on sale based on those observations

## What is included

- FastAPI API
- SQLite database
- demo data seeder with two years of synthetic price history
- analytics endpoints for price history and sale tendency

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will start at `http://127.0.0.1:8000`.

## Seed demo data

```bash
curl -X POST http://127.0.0.1:8000/seed-demo-data
```

## Useful endpoints

- `GET /health`
- `GET /brands`
- `GET /products`
- `GET /products/{product_id}/price-history?days=730`
- `GET /brands/{brand_id}/sale-calendar?days=730&sale_threshold=0.90`

## How sale detection works

For each product observation, the service compares the observed price against the product's median price over the selected lookback window.

If:

`observed_price <= median_price * sale_threshold`

then that observation is treated as a sale event.

The brand-level sale calendar groups those events by month and reports:

- sale event count
- total observations
- sale rate
- average discount percentage

## Suggested next steps

- replace demo seeding with retailer/API ingestion jobs
- normalize SKUs across retailers
- add alerting for unusually low prices
- build a dashboard UI for browsing sale calendars by brand and category
