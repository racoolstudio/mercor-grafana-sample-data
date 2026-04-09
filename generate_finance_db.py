import pymssql
import random
import time
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()
random.seed(None)

BRANCHES = [
    ("Manhattan HQ",       "New York",     "NY"),
    ("Brooklyn Branch",    "Brooklyn",     "NY"),
    ("LA Downtown",        "Los Angeles",  "CA"),
    ("Chicago Loop",       "Chicago",      "IL"),
    ("Houston Central",    "Houston",      "TX"),
    ("Phoenix West",       "Phoenix",      "AZ"),
    ("Philadelphia Main",  "Philadelphia", "PA"),
    ("San Antonio Branch", "San Antonio",  "TX"),
    ("San Diego Coast",    "San Diego",    "CA"),
    ("Dallas Uptown",      "Dallas",       "TX"),
    ("Miami South Beach",  "Miami",        "FL"),
    ("Seattle Pioneer",    "Seattle",      "WA"),
]

TX_CATEGORIES = ["groceries","dining","fuel","entertainment","healthcare",
                 "utilities","travel","shopping","transfer","atm_withdrawal"]
LOAN_TYPES    = ["personal","mortgage","auto","student","business","home_equity"]

def random_date(start_days_ago, end_days_ago=0):
    start = datetime.now() - timedelta(days=start_days_ago)
    end   = datetime.now() - timedelta(days=end_days_ago)
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

def wait_for_mssql(retries=30):
    for i in range(retries):
        try:
            c = pymssql.connect(host="127.0.0.1", port=1433,
                                user="sa", password="FinanceStr0ng!")
            c.close()
            return
        except Exception as e:
            print(f"  waiting for MSSQL... ({i+1}/{retries})")
            time.sleep(5)
    raise RuntimeError("MSSQL never became ready")

def run(conn, sql, params=None):
    cur = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()
    cur.close()

def build():
    wait_for_mssql()
    # Create DB in a separate autocommit connection
    conn0 = pymssql.connect(host="127.0.0.1", port=1433, user="sa", password="FinanceStr0ng!", autocommit=True)
    c0 = conn0.cursor()
    c0.execute("IF NOT EXISTS (SELECT * FROM sys.databases WHERE name='financedb') CREATE DATABASE financedb")
    conn0.close()

    conn = pymssql.connect(host="127.0.0.1", port=1433,
                           user="sa", password="FinanceStr0ng!", database="financedb")
    cur = conn.cursor()

    # Schema - drop in correct FK order
    for drop in ["loan_payments","loans","transactions","accounts","customers","branches"]:
        cur.execute(f"IF OBJECT_ID('{drop}','U') IS NOT NULL DROP TABLE [{drop}]")
        conn.commit()

    cur.execute("""
    CREATE TABLE branches (
        branch_id   INT IDENTITY PRIMARY KEY,
        name        NVARCHAR(100) NOT NULL,
        city        NVARCHAR(80),
        state       CHAR(2),
        opened_at   DATE,
        is_active   BIT DEFAULT 1
    )""")

    cur.execute("""
    CREATE TABLE customers (
        cust_id      INT IDENTITY PRIMARY KEY,
        first_name   NVARCHAR(60)  NOT NULL,
        last_name    NVARCHAR(60)  NOT NULL,
        email        NVARCHAR(160) UNIQUE NOT NULL,
        phone        NVARCHAR(20),
        credit_score SMALLINT,
        risk_tier    NVARCHAR(10),
        created_at   DATETIME      NOT NULL,
        branch_id    INT REFERENCES branches(branch_id)
    )""")

    cur.execute("""
    CREATE TABLE accounts (
        acc_id      INT IDENTITY PRIMARY KEY,
        cust_id     INT NOT NULL REFERENCES customers(cust_id),
        branch_id   INT NOT NULL REFERENCES branches(branch_id),
        acc_type    NVARCHAR(20) NOT NULL,
        balance     DECIMAL(14,2) NOT NULL,
        opened_at   DATETIME NOT NULL,
        status      NVARCHAR(15) DEFAULT 'active',
        interest_rate DECIMAL(5,3)
    )""")

    cur.execute("""
    CREATE TABLE transactions (
        txn_id      INT IDENTITY PRIMARY KEY,
        acc_id      INT NOT NULL REFERENCES accounts(acc_id),
        txn_type    NVARCHAR(15) NOT NULL,
        amount      DECIMAL(12,2) NOT NULL,
        balance_after DECIMAL(14,2),
        occurred_at DATETIME NOT NULL,
        category    NVARCHAR(30),
        description NVARCHAR(200),
        status      NVARCHAR(15) DEFAULT 'completed'
    )""")

    cur.execute("""
    CREATE TABLE loans (
        loan_id     INT IDENTITY PRIMARY KEY,
        cust_id     INT NOT NULL REFERENCES customers(cust_id),
        branch_id   INT NOT NULL REFERENCES branches(branch_id),
        loan_type   NVARCHAR(20) NOT NULL,
        principal   DECIMAL(14,2) NOT NULL,
        rate        DECIMAL(5,3) NOT NULL,
        term_months SMALLINT,
        status      NVARCHAR(15) DEFAULT 'active',
        issued_at   DATE,
        paid_off_at DATE
    )""")

    cur.execute("""
    CREATE TABLE loan_payments (
        pay_id   INT IDENTITY PRIMARY KEY,
        loan_id  INT NOT NULL REFERENCES loans(loan_id),
        amount   DECIMAL(12,2) NOT NULL,
        paid_at  DATETIME NOT NULL,
        status   NVARCHAR(15) DEFAULT 'paid'
    )""")
    conn.commit()

    # branches
    print("Generating branches...")
    branch_ids = []
    for name, city, state in BRANCHES:
        cur.execute("""INSERT INTO branches (name,city,state,opened_at,is_active)
                       OUTPUT INSERTED.branch_id VALUES (%s,%s,%s,%s,%s)""",
                    (name, city, state, random_date(3000, 365).date(), 1))
        branch_ids.append(cur.fetchone()[0])
    conn.commit()

    # customers
    print("Generating customers...")
    cust_ids = []
    for _ in range(3000):
        score = int(random.gauss(680, 90))
        score = max(300, min(850, score))
        tier = "prime" if score >= 720 else ("near_prime" if score >= 640 else "subprime")
        created = random_date(2000, 5)
        cur.execute("""INSERT INTO customers (first_name,last_name,email,phone,credit_score,risk_tier,created_at,branch_id)
                       OUTPUT INSERTED.cust_id VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (fake.first_name(), fake.last_name(), fake.unique.email(),
                     fake.numerify("(###) ###-####"),
                     score, tier, created.strftime("%Y-%m-%d %H:%M:%S"),
                     random.choice(branch_ids)))
        cust_ids.append(cur.fetchone()[0])
    conn.commit()

    # accounts + transactions
    print("Generating accounts and transactions...")
    acc_ids = []
    for cid in cust_ids:
        n_accs = random.choices([1,2,3], weights=[55,35,10])[0]
        for _ in range(n_accs):
            acc_type = random.choices(["checking","savings","checking","money_market","cd"],
                                       weights=[45,35,45,10,5])[0]
            balance  = round(random.lognormvariate(8, 1.5), 2)
            interest = round(random.uniform(0.01, 0.05) if acc_type in ("savings","cd","money_market") else 0, 3)
            opened   = random_date(1800, 30)
            status   = random.choices(["active","active","active","closed","frozen"],
                                       weights=[80,80,80,8,2])[0]
            cur.execute("""INSERT INTO accounts (cust_id,branch_id,acc_type,balance,opened_at,status,interest_rate)
                           OUTPUT INSERTED.acc_id VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                        (cid, random.choice(branch_ids), acc_type,
                         balance, opened.strftime("%Y-%m-%d %H:%M:%S"), status, interest))
            aid = cur.fetchone()[0]
            acc_ids.append(aid)

            # transactions
            n_tx = random.randint(5, 80)
            running_bal = balance
            txn_rows = []
            for _ in range(n_tx):
                txn_type = random.choices(["debit","credit","debit","debit"],weights=[50,30,50,50])[0]
                amt = round(random.lognormvariate(4, 1.2), 2)
                if txn_type == "debit":
                    running_bal -= amt
                else:
                    running_bal += amt
                txn_rows.append((aid, txn_type, amt, round(running_bal, 2),
                                 random_date(700, 0).strftime("%Y-%m-%d %H:%M:%S"),
                                 random.choice(TX_CATEGORIES),
                                 fake.sentence(nb_words=4),
                                 random.choices(["completed","completed","pending","failed"],
                                                weights=[85,85,8,2])[0]))
            if txn_rows:
                cur.executemany("""INSERT INTO transactions
                    (acc_id,txn_type,amount,balance_after,occurred_at,category,description,status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""", txn_rows)
    conn.commit()

    # loans
    print("Generating loans...")
    loan_ids = []
    for _ in range(1200):
        cid = random.choice(cust_ids)
        ltype = random.choice(LOAN_TYPES)
        principal = {
            "personal": random.uniform(1000, 50000),
            "mortgage": random.uniform(80000, 800000),
            "auto":     random.uniform(8000, 65000),
            "student":  random.uniform(5000, 120000),
            "business": random.uniform(10000, 500000),
            "home_equity": random.uniform(20000, 200000),
        }[ltype]
        rate   = round(random.uniform(2.5, 18.0), 3)
        term   = random.choice([12, 24, 36, 60, 84, 120, 180, 240, 360])
        issued = random_date(1500, 30)
        status = random.choices(["active","active","paid_off","defaulted"],weights=[60,60,20,5])[0]
        paid_off = None
        if status == "paid_off":
            paid_off = (issued + timedelta(days=term*30)).date()
        cur.execute("""INSERT INTO loans (cust_id,branch_id,loan_type,principal,rate,term_months,status,issued_at,paid_off_at)
                       OUTPUT INSERTED.loan_id VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (cid, random.choice(branch_ids), ltype, round(principal, 2), rate, term,
                     status, issued.date(), paid_off))
        loan_ids.append(cur.fetchone()[0])
    conn.commit()

    # loan payments
    print("Generating loan payments...")
    pay_rows = []
    for lid in loan_ids:
        for _ in range(random.randint(1, 24)):
            pay_rows.append((lid, round(random.uniform(200, 3000), 2),
                             random_date(500, 0).strftime("%Y-%m-%d %H:%M:%S"),
                             random.choices(["paid","paid","missed","late"],weights=[80,80,5,5])[0]))
        if len(pay_rows) >= 2000:
            cur.executemany("INSERT INTO loan_payments (loan_id,amount,paid_at,status) VALUES (%s,%s,%s,%s)", pay_rows)
            pay_rows = []
    if pay_rows:
        cur.executemany("INSERT INTO loan_payments (loan_id,amount,paid_at,status) VALUES (%s,%s,%s,%s)", pay_rows)
    conn.commit()

    cur.close()
    conn.close()
    print("\nDone! Financial database ready in MSSQL (financedb)")

if __name__ == "__main__":
    build()
