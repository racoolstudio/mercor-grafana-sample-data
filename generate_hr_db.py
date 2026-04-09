import psycopg2
import random
import time
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()
random.seed(None)

DEPARTMENTS = [
    ("Engineering",     180000, "San Francisco"),
    ("Product",         120000, "San Francisco"),
    ("Sales",           200000, "New York"),
    ("Marketing",        90000, "New York"),
    ("HR",               60000, "Chicago"),
    ("Finance",          80000, "Chicago"),
    ("Customer Success", 70000, "Austin"),
    ("Data & Analytics",110000, "San Francisco"),
    ("Legal",            55000, "New York"),
    ("Operations",       75000, "Austin"),
]

ROLES_BY_DEPT = {
    "Engineering":      ["Junior Engineer","Software Engineer","Senior Engineer","Staff Engineer","Engineering Manager"],
    "Product":          ["Associate PM","Product Manager","Senior PM","Group PM","VP of Product"],
    "Sales":            ["SDR","Account Executive","Senior AE","Sales Manager","VP of Sales"],
    "Marketing":        ["Marketing Coordinator","Marketing Manager","Sr. Marketing Manager","Director of Marketing"],
    "HR":               ["HR Coordinator","HR Business Partner","Sr. HRBP","HR Manager","Head of HR"],
    "Finance":          ["Financial Analyst","Sr. Financial Analyst","Finance Manager","Controller","CFO"],
    "Customer Success": ["CSM","Sr. CSM","CS Team Lead","Director of CS"],
    "Data & Analytics": ["Data Analyst","Sr. Data Analyst","Data Engineer","Analytics Manager"],
    "Legal":            ["Legal Counsel","Sr. Legal Counsel","Associate GC","General Counsel"],
    "Operations":       ["Operations Analyst","Operations Manager","Sr. Operations Manager","VP of Operations"],
}

SALARY_RANGE = {
    "Junior Engineer": (70000, 95000), "Software Engineer": (95000, 140000),
    "Senior Engineer": (140000, 185000), "Staff Engineer": (180000, 230000),
    "Engineering Manager": (170000, 220000),
    "Associate PM": (85000, 110000), "Product Manager": (110000, 150000),
    "Senior PM": (145000, 190000), "Group PM": (180000, 220000), "VP of Product": (200000, 260000),
    "SDR": (50000, 70000), "Account Executive": (70000, 100000),
    "Senior AE": (95000, 130000), "Sales Manager": (120000, 160000), "VP of Sales": (180000, 240000),
    "Marketing Coordinator": (50000, 65000), "Marketing Manager": (80000, 110000),
    "Sr. Marketing Manager": (105000, 140000), "Director of Marketing": (140000, 180000),
    "HR Coordinator": (45000, 60000), "HR Business Partner": (70000, 95000),
    "Sr. HRBP": (90000, 120000), "HR Manager": (110000, 145000), "Head of HR": (140000, 180000),
    "Financial Analyst": (65000, 90000), "Sr. Financial Analyst": (85000, 115000),
    "Finance Manager": (110000, 145000), "Controller": (140000, 180000), "CFO": (200000, 280000),
    "CSM": (60000, 85000), "Sr. CSM": (80000, 110000),
    "CS Team Lead": (100000, 130000), "Director of CS": (130000, 170000),
    "Data Analyst": (75000, 100000), "Sr. Data Analyst": (95000, 130000),
    "Data Engineer": (110000, 150000), "Analytics Manager": (130000, 170000),
    "Legal Counsel": (100000, 140000), "Sr. Legal Counsel": (130000, 170000),
    "Associate GC": (160000, 210000), "General Counsel": (200000, 270000),
    "Operations Analyst": (55000, 75000), "Operations Manager": (90000, 120000),
    "Sr. Operations Manager": (110000, 145000), "VP of Operations": (160000, 210000),
}

def random_date(start_days_ago, end_days_ago=0):
    start = datetime.now() - timedelta(days=start_days_ago)
    end   = datetime.now() - timedelta(days=end_days_ago)
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

def wait_for_pg(cfg, retries=20):
    for i in range(retries):
        try:
            c = psycopg2.connect(**cfg)
            c.close()
            return
        except Exception:
            print(f"  waiting for PostgreSQL... ({i+1}/{retries})")
            time.sleep(3)
    raise RuntimeError("PostgreSQL never became ready")

def build():
    cfg = dict(host="127.0.0.1", port=5432, dbname="hrdb", user="grafana", password="grafanapass")
    wait_for_pg(cfg)
    conn = psycopg2.connect(**cfg)
    conn.autocommit = False
    cur = conn.cursor()

    cur.execute("""
    DROP TABLE IF EXISTS performance_reviews CASCADE;
    DROP TABLE IF EXISTS attendance CASCADE;
    DROP TABLE IF EXISTS salaries CASCADE;
    DROP TABLE IF EXISTS job_postings CASCADE;
    DROP TABLE IF EXISTS employees CASCADE;
    DROP TABLE IF EXISTS departments CASCADE;

    CREATE TABLE departments (
        dept_id     SERIAL PRIMARY KEY,
        name        VARCHAR(80)  NOT NULL,
        budget      BIGINT,
        location    VARCHAR(80),
        head_count  INT DEFAULT 0
    );

    CREATE TABLE employees (
        emp_id      SERIAL PRIMARY KEY,
        first_name  VARCHAR(60)  NOT NULL,
        last_name   VARCHAR(60)  NOT NULL,
        email       VARCHAR(160) UNIQUE NOT NULL,
        dept_id     INT REFERENCES departments(dept_id),
        role        VARCHAR(80),
        hire_date   DATE         NOT NULL,
        status      VARCHAR(20)  DEFAULT 'active',
        gender      VARCHAR(10),
        age         INT
    );

    CREATE TABLE salaries (
        salary_id      SERIAL PRIMARY KEY,
        emp_id         INT REFERENCES employees(emp_id),
        amount         NUMERIC(12,2) NOT NULL,
        effective_date DATE          NOT NULL,
        salary_type    VARCHAR(20)   DEFAULT 'base'
    );

    CREATE TABLE attendance (
        att_id       SERIAL PRIMARY KEY,
        emp_id       INT REFERENCES employees(emp_id),
        att_date     DATE    NOT NULL,
        check_in     TIME,
        check_out    TIME,
        hours_worked NUMERIC(4,2),
        status       VARCHAR(20) DEFAULT 'present'
    );

    CREATE TABLE performance_reviews (
        review_id   SERIAL PRIMARY KEY,
        emp_id      INT REFERENCES employees(emp_id),
        reviewer_id INT REFERENCES employees(emp_id),
        score       NUMERIC(3,1),
        period      VARCHAR(20),
        comments    TEXT,
        created_at  DATE NOT NULL
    );

    CREATE TABLE job_postings (
        post_id      SERIAL PRIMARY KEY,
        dept_id      INT REFERENCES departments(dept_id),
        title        VARCHAR(100),
        status       VARCHAR(20) DEFAULT 'open',
        posted_at    DATE,
        closed_at    DATE,
        applicants   INT DEFAULT 0
    );
    """)
    conn.commit()

    # departments
    print("Generating departments...")
    dept_ids = []
    for name, budget, location in DEPARTMENTS:
        cur.execute("INSERT INTO departments (name, budget, location) VALUES (%s,%s,%s) RETURNING dept_id",
                    (name, budget, location))
        dept_ids.append((cur.fetchone()[0], name))
    conn.commit()

    # employees
    print("Generating employees...")
    emp_ids = []
    dept_emp_count = {d[0]: 0 for d in dept_ids}
    for _ in range(850):
        dept_id, dept_name = random.choice(dept_ids)
        role = random.choice(ROLES_BY_DEPT[dept_name])
        hire = random_date(2500, 10)
        status = random.choices(["active","active","active","inactive","on_leave"],
                                weights=[80,80,80,10,5])[0]
        gender = random.choice(["M","F","M","F","Non-binary"])
        cur.execute("""INSERT INTO employees (first_name,last_name,email,dept_id,role,hire_date,status,gender,age)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING emp_id""",
                    (fake.first_name(), fake.last_name(), fake.unique.email(),
                     dept_id, role, hire.date(), status, gender, random.randint(22, 62)))
        eid = cur.fetchone()[0]
        emp_ids.append(eid)
        dept_emp_count[dept_id] += 1

        # salary history
        lo, hi = SALARY_RANGE.get(role, (50000, 100000))
        base = round(random.uniform(lo, hi), -2)
        sal_date = hire
        while sal_date < datetime.now():
            cur.execute("INSERT INTO salaries (emp_id,amount,effective_date,salary_type) VALUES (%s,%s,%s,%s)",
                        (eid, base, sal_date.date(), "base"))
            base = round(base * random.uniform(1.02, 1.08), -2)
            sal_date += timedelta(days=365)

    for dept_id, _ in dept_ids:
        cur.execute("UPDATE departments SET head_count=%s WHERE dept_id=%s",
                    (dept_emp_count[dept_id], dept_id))
    conn.commit()

    # attendance (last 180 days)
    print("Generating attendance...")
    att_rows = []
    for eid in random.sample(emp_ids, min(400, len(emp_ids))):
        for d in range(180):
            day = (datetime.now() - timedelta(days=d)).date()
            if day.weekday() >= 5:
                continue
            status = random.choices(["present","present","present","absent","remote","half_day"],
                                    weights=[60,60,60,5,20,5])[0]
            if status in ("absent",):
                att_rows.append((eid, day, None, None, None, status))
            else:
                ci_h = random.randint(7, 10)
                ci_m = random.randint(0, 59)
                hrs = round(random.uniform(6.5, 9.5), 1) if status != "half_day" else round(random.uniform(3.5, 5.0), 1)
                co_h = ci_h + int(hrs)
                att_rows.append((eid, day, f"{ci_h:02d}:{ci_m:02d}", f"{co_h:02d}:{ci_m:02d}", hrs, status))
        if len(att_rows) >= 5000:
            cur.executemany("INSERT INTO attendance (emp_id,att_date,check_in,check_out,hours_worked,status) VALUES (%s,%s,%s,%s,%s,%s)", att_rows)
            att_rows = []
    if att_rows:
        cur.executemany("INSERT INTO attendance (emp_id,att_date,check_in,check_out,hours_worked,status) VALUES (%s,%s,%s,%s,%s,%s)", att_rows)
    conn.commit()

    # performance reviews
    print("Generating performance reviews...")
    periods = ["Q1 2024","Q2 2024","Q3 2024","Q4 2024","Q1 2025","Q2 2025","Q3 2025"]
    comments_pool = [
        "Consistently exceeds expectations.", "Strong performer, great team player.",
        "Meets expectations, room to grow.", "Shows initiative and leadership.",
        "Needs improvement in communication.", "Excellent technical skills.",
        "Great attitude, developing fast.", "Below expectations this quarter.",
    ]
    rev_rows = []
    for eid in emp_ids:
        for period in random.sample(periods, k=random.randint(1, 3)):
            reviewer = random.choice(emp_ids)
            score = round(random.choices(
                [5.0, 4.5, 4.0, 3.5, 3.0, 2.5, 2.0],
                weights=[10, 20, 30, 20, 12, 5, 3])[0], 1)
            rev_rows.append((eid, reviewer, score, period,
                             random.choice(comments_pool),
                             random_date(500, 10).date()))
    cur.executemany("""INSERT INTO performance_reviews
        (emp_id,reviewer_id,score,period,comments,created_at) VALUES (%s,%s,%s,%s,%s,%s)""", rev_rows)
    conn.commit()

    # job postings
    print("Generating job postings...")
    for dept_id, dept_name in dept_ids:
        for _ in range(random.randint(1, 5)):
            role = random.choice(ROLES_BY_DEPT[dept_name])
            posted = random_date(300, 10)
            status = random.choices(["open","closed","open"],weights=[50,40,50])[0]
            closed = None
            if status == "closed":
                closed = (posted + timedelta(days=random.randint(14, 90))).date()
            cur.execute("""INSERT INTO job_postings (dept_id,title,status,posted_at,closed_at,applicants)
                           VALUES (%s,%s,%s,%s,%s,%s)""",
                        (dept_id, role, status, posted.date(), closed, random.randint(5, 280)))
    conn.commit()

    cur.close()
    conn.close()
    print("\nDone! HR database ready in PostgreSQL (hrdb)")

if __name__ == "__main__":
    build()
