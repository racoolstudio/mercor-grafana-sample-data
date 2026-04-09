#!/bin/bash
set -e
cd "$(dirname "$0")"

DOCKER="/usr/local/bin/docker"
# Auto-detect python with required packages
if python3 -c "import faker" 2>/dev/null; then
  PYTHON="python3"
else
  PYTHON="/usr/bin/python3"
fi
export PYTHONPATH="/Users/racool/Library/Python/3.9/lib/python/site-packages:$PYTHONPATH"

echo "======================================================"
echo "  Mercor Grafana Sample Data Stack — Setup"
echo "======================================================"

echo ""
echo "[1/3] Starting all containers..."
$DOCKER compose up --detach
echo "Waiting 30s for databases to initialize..."
sleep 30

echo ""
echo "[2/3] Generating data..."
echo "  → SaaS (MySQL)..."
$PYTHON generate_saas_db.py

echo "  → HR (PostgreSQL)..."
$PYTHON generate_hr_db.py

echo "  → IoT/Monitoring (InfluxDB)..."
$PYTHON generate_iot_db.py

echo "  → Financial (MSSQL)..."
$PYTHON generate_finance_db.py

echo "  → E-commerce (SQLite already included)"

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
