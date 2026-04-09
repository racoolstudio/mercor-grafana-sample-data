# Mercor Grafana Sample Data Stack

A realistic, multi-domain analytics platform with 6 pre-built Grafana dashboards connected to 6 different databases — all populated with synthetic data.

**Docker Hub:** [`racoolstudio/grafana-synthetic-data`](https://hub.docker.com/r/racoolstudio/grafana-synthetic-data)

---

## Dashboards

| Dashboard | Database | Domain | Data Volume |
|---|---|---|---|
| E-commerce Overview | SQLite | Orders, customers, products | ~45K rows |
| SaaS Analytics | MySQL 8.0 | MRR, subscriptions, churn | ~30K rows |
| HR Analytics | PostgreSQL 15 | Employees, salaries, attendance | ~50K rows |
| IoT & Server Monitoring | InfluxDB 2.7 | CPU, sensors, API metrics | ~500K points |
| Financial & Banking | MS SQL Server 2022 | Transactions, loans, branches | ~80K rows |
| Infrastructure | Prometheus | Real-time host metrics | Live |

---

## Quick Start

### Option A — From Docker Hub (recommended)
\`\`\`bash
docker compose -f docker-compose.hub.yml up -d
pip3 install faker psycopg2-binary influxdb-client pymssql mysql-connector-python
chmod +x setup.sh && ./setup.sh
# Open http://localhost:3000  →  admin / admin123
\`\`\`

### Option B — Build locally
\`\`\`bash
curl -L -o frser-sqlite-datasource.zip \
  https://github.com/fr-ser/grafana-sqlite-datasource/releases/download/v3.4.0/frser-sqlite-datasource-3.4.0.zip
docker compose up --build -d && ./setup.sh
\`\`\`

---

## Visualization Types

| Type | Purpose |
|---|---|
| Stat | KPI numbers |
| Time series | Trends over time |
| Gauge | Circular with thresholds (green/yellow/red) |
| Bar gauge | Horizontal gradient category comparisons |
| Candlestick | Daily OHLC for revenue & transactions |
| Table | Color-coded top-N lists |
| Bar chart | Distributions and rankings |

---

## Ports & Credentials

| Service | Port | User | Password |
|---|---|---|---|
| Grafana | 3000 | admin | admin123 |
| MySQL | 3307 | grafana | grafanapass |
| PostgreSQL | 5432 | grafana | grafanapass |
| InfluxDB | 8086 | admin | adminpass123 |
| MS SQL Server | 1433 | sa | FinanceStr0ng! |
| Prometheus | 9090 | — | — |

InfluxDB token: `myinfluxtoken123456` · org: `myorg` · bucket: `iot`

---

## Publish Updates to Docker Hub

\`\`\`bash
docker build -t racoolstudio/grafana-synthetic-data:latest .
docker login --username racoolstudio
./push.sh
\`\`\`

## Requirements

- Docker Desktop with 8GB+ RAM
- 10GB free disk space
- Python 3.9+ (data generation only)
