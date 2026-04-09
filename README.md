# Mercor Grafana Sample Data Stack

A realistic, multi-domain analytics platform with **6 pre-built Grafana dashboards** connected to **6 different databases** — all populated with synthetic data.

**Docker Hub:** [`racoolstudio/grafana-synthetic-data`](https://hub.docker.com/r/racoolstudio/grafana-synthetic-data)

---

## Dashboards

| Dashboard | URL | Database | Domain | Data Volume |
|---|---|---|---|---|
| E-commerce Overview | `/d/ecommerce-main` | SQLite | Orders, customers, products | ~45K rows |
| SaaS Analytics | `/d/saas-main` | MySQL 8.0 | MRR, subscriptions, churn | ~30K rows |
| HR Analytics | `/d/hr-main` | PostgreSQL 15 | Employees, salaries, attendance | ~50K rows |
| IoT & Server Monitoring | `/d/iot-main` | InfluxDB 2.7 | CPU, sensors, API metrics | ~500K points |
| Financial & Banking | `/d/finance-main` | MS SQL Server 2022 | Transactions, loans, branches | ~80K rows |
| Infrastructure | `/d/infra-main` | Prometheus | Real-time host metrics | Live |

---

## Quick Start (Docker Hub)

> No cloning or building required. Just pull and run.

**Step 1 — Pull the image from Docker Hub**
```bash
docker pull racoolstudio/grafana-synthetic-data:latest
```

**Step 2 — Get the config files**
```bash
curl -O https://raw.githubusercontent.com/racoolstudio/grafana-synthetic-data/main/docker-compose.hub.yml
curl -O https://raw.githubusercontent.com/racoolstudio/grafana-synthetic-data/main/prometheus.yml
```

**Step 3 — Start all containers**
```bash
docker compose -f docker-compose.hub.yml up -d
```

**Step 4 — Install Python deps & generate data**
```bash
pip3 install faker psycopg2-binary influxdb-client pymssql mysql-connector-python

curl -O https://raw.githubusercontent.com/racoolstudio/grafana-synthetic-data/main/setup.sh
curl -O https://raw.githubusercontent.com/racoolstudio/grafana-synthetic-data/main/generate_saas_db.py
curl -O https://raw.githubusercontent.com/racoolstudio/grafana-synthetic-data/main/generate_hr_db.py
curl -O https://raw.githubusercontent.com/racoolstudio/grafana-synthetic-data/main/generate_iot_db.py
curl -O https://raw.githubusercontent.com/racoolstudio/grafana-synthetic-data/main/generate_finance_db.py

chmod +x setup.sh && ./setup.sh
```

**Step 5 — Open Grafana**
```
http://localhost:3000
Username: admin
Password: admin123
```

> The **E-commerce dashboard** works immediately — SQLite DB is baked into the image.
> The other 5 dashboards need the generators to run once (Step 3).

---

## Quick Start (Clone & Build)

```bash
git clone https://github.com/racoolstudio/grafana-synthetic-data.git
cd grafana-synthetic-data

# Download SQLite plugin
curl -L -o frser-sqlite-datasource.zip \
  https://github.com/fr-ser/grafana-sqlite-datasource/releases/download/v3.4.0/frser-sqlite-datasource-3.4.0.zip

# Build and start
docker compose up --build -d

# Generate data
pip3 install faker psycopg2-binary influxdb-client pymssql mysql-connector-python
chmod +x setup.sh && ./setup.sh
```

---

## Visualization Types

| Panel Type | Used In | Purpose |
|---|---|---|
| Stat | All dashboards | KPI numbers with color |
| Time series | All dashboards | Trends over time |
| Gauge | IoT, Infra, SaaS, HR | Circular with green/yellow/red thresholds |
| Bar gauge | All dashboards | Horizontal gradient category comparisons |
| Candlestick | E-commerce, Finance | Daily OHLC for revenue & transactions |
| Table | E-commerce, SaaS, HR, Finance | Color-coded top-N lists |
| Bar chart | All dashboards | Distributions and rankings |

---

## Ports

| Service | Port |
|---|---|
| Grafana | 3000 |
| MySQL (SaaS) | 3307 |
| PostgreSQL (HR) | 5432 |
| InfluxDB (IoT) | 8086 |
| MS SQL Server (Finance) | 1433 |
| Prometheus | 9090 |
| Node Exporter | 9100 |

---

## Credentials

| Service | User | Password |
|---|---|---|
| Grafana | `admin` | `admin123` |
| MySQL | `grafana` | `grafanapass` |
| PostgreSQL | `grafana` | `grafanapass` |
| InfluxDB | `admin` | `adminpass123` |
| MS SQL Server | `sa` | `FinanceStr0ng!` |

InfluxDB: token `myinfluxtoken123456` · org `myorg` · bucket `iot`

---

## Project Structure

```
mercor-grafana-sample-data/
├── docker-compose.yml           # Local build
├── docker-compose.hub.yml       # Docker Hub pull
├── Dockerfile                   # Custom Grafana image
├── prometheus.yml               # Prometheus scrape config
├── ecommerce.db                 # SQLite DB (pre-populated, baked into image)
├── setup.sh                     # One-command setup
├── push.sh                      # Docker Hub push script
├── generate_db.py               # E-commerce data (SQLite)
├── generate_saas_db.py          # SaaS data (MySQL)
├── generate_hr_db.py            # HR data (PostgreSQL)
├── generate_iot_db.py           # IoT data (InfluxDB)
├── generate_finance_db.py       # Finance data (MSSQL)
└── grafana/provisioning/
    ├── datasources/             # Auto-provisioned connections
    └── dashboards/              # Auto-provisioned dashboards
```

---

## Requirements

- Docker Desktop with **8GB+ RAM** allocated
- **10GB** free disk space
- Python 3.9+ (for data generation only)

---

## Rebuild & Publish

```bash
docker build -t racoolstudio/grafana-synthetic-data:latest .
docker login --username racoolstudio
./push.sh
```
