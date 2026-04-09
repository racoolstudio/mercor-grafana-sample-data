# Ecommerce DB + Grafana Dashboard

## What's included
- `ecommerce.db` — SQLite database with 7 tables and ~45,000 rows of realistic data
- `generate_db.py` — regenerate the DB anytime with fresh random data
- `docker-compose.yml` — spins up Grafana with the SQLite plugin pre-installed
- `grafana/` — auto-provisions the datasource and dashboard on first launch

## Tables
| Table | Rows | Description |
|---|---|---|
| customers | 2,000 | Names, emails, locations, loyalty points |
| products | 50 | Real product names across 5 categories |
| orders | 8,000 | Orders with status, payment, shipping, discounts |
| order_items | ~14,000 | Line items linked to orders and products |
| sessions | 15,000 | Web sessions with device, source, conversion |
| reviews | ~4,800 | Product reviews with ratings and text |
| support_tickets | 1,200 | Customer support cases with resolution times |

## How to run

### Step 1 — Generate the database (only needed if ecommerce.db is missing)
```bash
pip install faker
python3 generate_db.py
```

### Step 2 — Start Grafana
```bash
docker-compose up -d
```

### Step 3 — Open Grafana
Go to http://localhost:3000
- Username: admin
- Password: admin123

The Ecommerce Overview dashboard loads automatically.

## Regenerate fresh data anytime
```bash
python3 generate_db.py
# then restart grafana
docker-compose restart
```
