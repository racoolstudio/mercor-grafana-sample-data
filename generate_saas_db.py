import mysql.connector
import random
from faker import Faker
from datetime import datetime, timedelta
import time

fake = Faker()
random.seed(None)

PLANS = {
    "starter":    {"price": 29,   "max_users": 5,   "weight": 40},
    "growth":     {"price": 99,   "max_users": 25,  "weight": 35},
    "business":   {"price": 299,  "max_users": 100, "weight": 18},
    "enterprise": {"price": 999,  "max_users": 999, "weight": 7},
}

INDUSTRIES = ["SaaS", "E-commerce", "Healthcare", "Finance", "Education",
               "Real Estate", "Marketing", "Logistics", "Legal", "HR Tech"]

FEATURES = ["dashboard", "reports", "api_access", "integrations", "sso",
            "audit_log", "custom_roles", "webhooks", "data_export", "ai_insights"]

CHURN_REASONS = [
    "Too expensive", "Missing features", "Switched to competitor",
    "Company shutdown", "No longer needed", "Poor support", None, None, None, None
]

def random_date(start_days_ago, end_days_ago=0):
    start = datetime.now() - timedelta(days=start_days_ago)
    end   = datetime.now() - timedelta(days=end_days_ago)
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

def wait_for_mysql(cfg, retries=20):
    for i in range(retries):
        try:
            c = mysql.connector.connect(**cfg)
            c.close()
            return True
        except Exception:
            print(f"  waiting for MySQL... ({i+1}/{retries})")
            time.sleep(3)
    raise RuntimeError("MySQL never became ready")

def build():
    cfg = dict(host="127.0.0.1", port=3307, user="grafana",
               password="grafanapass", database="saasdb")
    wait_for_mysql(cfg)
    conn = mysql.connector.connect(**cfg)
    cur  = conn.cursor()

    # ── schema ──────────────────────────────────────────────────────────
    for stmt in """
DROP TABLE IF EXISTS feature_usage;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS accounts;

CREATE TABLE accounts (
    account_id    INT AUTO_INCREMENT PRIMARY KEY,
    company_name  VARCHAR(120) NOT NULL,
    industry      VARCHAR(60),
    country       VARCHAR(60),
    city          VARCHAR(80),
    employee_count INT,
    created_at    DATETIME NOT NULL,
    health_score  TINYINT DEFAULT 80
);

CREATE TABLE subscriptions (
    sub_id        INT AUTO_INCREMENT PRIMARY KEY,
    account_id    INT NOT NULL,
    plan          VARCHAR(30) NOT NULL,
    mrr           DECIMAL(10,2) NOT NULL,
    status        ENUM('active','churned','paused','trial') NOT NULL,
    started_at    DATETIME NOT NULL,
    churned_at    DATETIME,
    churn_reason  VARCHAR(120),
    billing_cycle ENUM('monthly','annual') NOT NULL,
    discount_pct  TINYINT DEFAULT 0,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

CREATE TABLE users (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    account_id    INT NOT NULL,
    email         VARCHAR(160) UNIQUE NOT NULL,
    role          ENUM('owner','admin','member','viewer') NOT NULL,
    joined_at     DATETIME NOT NULL,
    last_active   DATETIME,
    is_active     TINYINT DEFAULT 1,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

CREATE TABLE invoices (
    invoice_id    INT AUTO_INCREMENT PRIMARY KEY,
    account_id    INT NOT NULL,
    sub_id        INT NOT NULL,
    amount        DECIMAL(10,2) NOT NULL,
    status        ENUM('paid','failed','pending','refunded') NOT NULL,
    issued_at     DATETIME NOT NULL,
    paid_at       DATETIME,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (sub_id)     REFERENCES subscriptions(sub_id)
);

CREATE TABLE events (
    event_id      INT AUTO_INCREMENT PRIMARY KEY,
    account_id    INT NOT NULL,
    user_id       INT,
    event_type    VARCHAR(60) NOT NULL,
    occurred_at   DATETIME NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

CREATE TABLE feature_usage (
    usage_id      INT AUTO_INCREMENT PRIMARY KEY,
    account_id    INT NOT NULL,
    feature       VARCHAR(60) NOT NULL,
    used_at       DATE NOT NULL,
    session_count INT DEFAULT 1,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);
""".strip().split(";"):
        s = stmt.strip()
        if s:
            cur.execute(s)
    conn.commit()

    # ── accounts ─────────────────────────────────────────────────────────
    print("Generating accounts...")
    account_ids = []
    for _ in range(600):
        created = random_date(900, 10)
        cur.execute("""INSERT INTO accounts
            (company_name, industry, country, city, employee_count, created_at, health_score)
            VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (fake.company(), random.choice(INDUSTRIES),
             random.choices(["US","US","US","UK","Canada","Australia","Germany","France"], weights=[40,40,40,10,8,5,4,3])[0],
             fake.city(),
             random.choice([1,5,10,25,50,100,250,500,1000,5000]),
             created.strftime("%Y-%m-%d %H:%M:%S"),
             random.randint(20, 100)))
        account_ids.append(cur.lastrowid)
    conn.commit()

    # ── subscriptions ────────────────────────────────────────────────────
    print("Generating subscriptions...")
    sub_ids = []
    plan_names  = list(PLANS.keys())
    plan_weights = [PLANS[p]["weight"] for p in plan_names]
    for acid in account_ids:
        created = random_date(900, 10)
        plan = random.choices(plan_names, weights=plan_weights)[0]
        base_price = PLANS[plan]["price"]
        billing = random.choices(["monthly","annual"], weights=[55,45])[0]
        discount = random.choices([0,0,0,10,15,20], weights=[50,20,10,10,6,4])[0]
        if billing == "annual":
            discount = max(discount, 10)
        mrr = round(base_price * (1 - discount/100) * (1 if billing=="monthly" else 1), 2)
        # churn: ~14% of accounts
        churned = random.random() < 0.14
        status = "churned" if churned else random.choices(
            ["active","active","active","active","trial","paused"], weights=[70,70,70,70,10,5])[0]
        churned_at = churn_reason = None
        if churned:
            churned_at = (created + timedelta(days=random.randint(30, 500))).strftime("%Y-%m-%d %H:%M:%S")
            churn_reason = random.choice(CHURN_REASONS)
        cur.execute("""INSERT INTO subscriptions
            (account_id, plan, mrr, status, started_at, churned_at, churn_reason, billing_cycle, discount_pct)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (acid, plan, mrr, status,
             created.strftime("%Y-%m-%d %H:%M:%S"),
             churned_at, churn_reason, billing, discount))
        sub_ids.append((cur.lastrowid, acid, mrr, status, created))
    conn.commit()

    # ── users ────────────────────────────────────────────────────────────
    print("Generating users...")
    user_ids_by_account = {}
    for acid in account_ids:
        n = random.choices([1,2,3,5,8,15,30], weights=[20,25,20,15,10,6,4])[0]
        user_ids_by_account[acid] = []
        for i in range(n):
            joined = random_date(850, 5)
            last_active = joined + timedelta(days=random.randint(1, 400))
            role = "owner" if i == 0 else random.choices(
                ["admin","member","member","member","viewer"], weights=[10,40,40,40,10])[0]
            email = fake.unique.email()
            cur.execute("""INSERT INTO users
                (account_id, email, role, joined_at, last_active, is_active)
                VALUES (%s,%s,%s,%s,%s,%s)""",
                (acid, email, role,
                 joined.strftime("%Y-%m-%d %H:%M:%S"),
                 last_active.strftime("%Y-%m-%d %H:%M:%S"),
                 random.choices([1,0], weights=[88,12])[0]))
            user_ids_by_account[acid].append(cur.lastrowid)
    conn.commit()

    # ── invoices ─────────────────────────────────────────────────────────
    print("Generating invoices...")
    for sid, acid, mrr, status, started in sub_ids:
        months = random.randint(1, 24)
        for m in range(months):
            issued = started + timedelta(days=30 * m)
            if issued > datetime.now():
                break
            pay_status = random.choices(
                ["paid","paid","paid","failed","pending","refunded"],
                weights=[80,80,80,8,5,3])[0]
            paid_at = None
            if pay_status == "paid":
                paid_at = (issued + timedelta(hours=random.randint(0, 48))).strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("""INSERT INTO invoices
                (account_id, sub_id, amount, status, issued_at, paid_at)
                VALUES (%s,%s,%s,%s,%s,%s)""",
                (acid, sid, mrr, pay_status,
                 issued.strftime("%Y-%m-%d %H:%M:%S"), paid_at))
    conn.commit()

    # ── events ───────────────────────────────────────────────────────────
    print("Generating events...")
    event_types = [
        "login","login","login","login",
        "dashboard_view","report_generated","export_csv",
        "integration_connected","api_call","settings_changed",
        "user_invited","billing_updated","password_reset","logout"
    ]
    batch = []
    for acid in account_ids:
        uids = user_ids_by_account.get(acid, [None])
        for _ in range(random.randint(10, 120)):
            batch.append((
                acid,
                random.choice(uids),
                random.choice(event_types),
                random_date(365, 0).strftime("%Y-%m-%d %H:%M:%S")
            ))
        if len(batch) >= 2000:
            cur.executemany("INSERT INTO events (account_id,user_id,event_type,occurred_at) VALUES (%s,%s,%s,%s)", batch)
            batch = []
    if batch:
        cur.executemany("INSERT INTO events (account_id,user_id,event_type,occurred_at) VALUES (%s,%s,%s,%s)", batch)
    conn.commit()

    # ── feature_usage ────────────────────────────────────────────────────
    print("Generating feature usage...")
    batch = []
    for acid in account_ids:
        for feat in random.sample(FEATURES, k=random.randint(2, len(FEATURES))):
            for _ in range(random.randint(1, 60)):
                d = random_date(180, 0).date()
                batch.append((acid, feat, d.strftime("%Y-%m-%d"), random.randint(1, 20)))
        if len(batch) >= 3000:
            cur.executemany("INSERT INTO feature_usage (account_id,feature,used_at,session_count) VALUES (%s,%s,%s,%s)", batch)
            batch = []
    if batch:
        cur.executemany("INSERT INTO feature_usage (account_id,feature,used_at,session_count) VALUES (%s,%s,%s,%s)", batch)
    conn.commit()

    cur.close()
    conn.close()
    print("\nDone! SaaS database ready in MySQL (saasdb)")

if __name__ == "__main__":
    build()
