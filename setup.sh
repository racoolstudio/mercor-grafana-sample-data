#!/bin/bash
set -e
cd "$(dirname "$0")"

DOCKER="/usr/local/bin/docker"

echo "======================================================"
echo "  Multi-Datasource Analytics Stack - Setup"
echo "======================================================"

echo ""
echo "[1/3] Starting all containers..."
$DOCKER compose up --detach
echo "Waiting 30s for databases to initialize..."
sleep 30

echo ""
echo "[2/3] Generating data..."
echo "  → SaaS (MySQL)..."
python3 generate_saas_db.py

echo "  → HR (PostgreSQL)..."
python3 generate_hr_db.py

echo "  → IoT/Monitoring (InfluxDB)..."
python3 generate_iot_db.py

echo "  → Financial (MSSQL)..."
python3 generate_finance_db.py

echo "  → E-commerce DB already exists (SQLite)"

echo ""
echo "[3/3] Restarting Grafana to reload provisioning..."
$DOCKER compose restart grafana
sleep 5

echo ""
echo "======================================================"
echo "  DONE! Open http://localhost:3000 (admin / admin123)"
echo ""
echo "  Dashboards:"
echo "    E-commerce  →  /d/ecommerce-main  (SQLite)"
echo "    SaaS        →  /d/saas-main       (MySQL)"
echo "    HR          →  /d/hr-main         (PostgreSQL)"
echo "    IoT         →  /d/iot-main        (InfluxDB)"
echo "    Finance     →  /d/finance-main    (MSSQL)"
echo "    Infra       →  /d/infra-main      (Prometheus)"
echo "======================================================"
