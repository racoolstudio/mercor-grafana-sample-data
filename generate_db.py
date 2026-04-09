import sqlite3
import random
from faker import Faker
from datetime import datetime, timedelta
import os

fake = Faker()
random.seed(None)  # true randomness each run

DB_PATH = "ecommerce.db"

# --- realistic product catalog ---
CATEGORIES = {
    "Electronics": [
        ("Sony WH-1000XM5 Headphones", 349.99, 289.00),
        ("Logitech MX Master 3 Mouse", 99.99, 72.00),
        ("Samsung 27\" Monitor", 329.99, 240.00),
        ("Anker USB-C Hub 7-in-1", 45.99, 22.00),
        ("Apple AirPods Pro 2nd Gen", 249.00, 180.00),
        ("Razer DeathAdder V3", 69.99, 38.00),
        ("Keychron K2 Mechanical Keyboard", 89.00, 52.00),
        ("Elgato Stream Deck MK.2", 149.99, 95.00),
        ("Rode NT-USB Mini Microphone", 99.00, 58.00),
        ("Webcam Logitech C920s", 79.99, 44.00),
    ],
    "Clothing": [
        ("Levi's 511 Slim Jeans", 69.50, 28.00),
        ("Nike Air Force 1 '07", 110.00, 55.00),
        ("Patagonia Better Sweater Fleece", 139.00, 70.00),
        ("Uniqlo Ultra Light Down Jacket", 89.90, 38.00),
        ("Carhartt WIP Chase Hoodie", 108.00, 52.00),
        ("Adidas Ultraboost 22", 190.00, 95.00),
        ("Columbia Watertight II Jacket", 100.00, 48.00),
        ("Champion Reverse Weave Sweatpants", 55.00, 22.00),
        ("Merrell Moab 3 Hiking Boots", 130.00, 68.00),
        ("Bombas Ankle Socks 6-Pack", 48.00, 18.00),
    ],
    "Home & Kitchen": [
        ("Instant Pot Duo 7-in-1", 99.95, 52.00),
        ("Vitamix 5200 Blender", 549.95, 310.00),
        ("Cuisinart 12-Cup Coffee Maker", 79.95, 38.00),
        ("Lodge 12\" Cast Iron Skillet", 49.90, 22.00),
        ("Dyson V8 Cordless Vacuum", 449.99, 275.00),
        ("Nespresso Vertuo Next", 159.00, 88.00),
        ("Brita Large 10-Cup Water Filter", 32.99, 14.00),
        ("OXO Good Grips 3-Piece Mixing Bowl", 28.99, 12.00),
        ("Rubbermaid Brilliance Storage Set", 39.99, 18.00),
        ("KitchenAid Stand Mixer 5-Qt", 449.99, 260.00),
    ],
    "Sports & Outdoors": [
        ("Hydro Flask 32oz Water Bottle", 49.95, 20.00),
        ("Osprey Atmos AG 65 Backpack", 290.00, 155.00),
        ("Garmin Forerunner 255", 349.99, 210.00),
        ("TRX Home2 Suspension Trainer", 189.95, 90.00),
        ("Manduka PRO Yoga Mat", 120.00, 55.00),
        ("Black Diamond Spot 400 Headlamp", 49.95, 22.00),
        ("Coleman Sundome 4-Person Tent", 119.99, 58.00),
        ("Tumaz Foam Roller", 25.99, 9.00),
        ("Resistance Bands Set WSAKOUE", 19.99, 6.00),
        ("NordicTrack T 6.5 S Treadmill", 649.00, 380.00),
    ],
    "Books": [
        ("Atomic Habits - James Clear", 16.99, 4.50),
        ("The Pragmatic Programmer", 49.95, 18.00),
        ("Designing Data-Intensive Applications", 59.99, 22.00),
        ("The Psychology of Money", 14.99, 4.00),
        ("Clean Code - Robert Martin", 39.99, 16.00),
        ("Dune - Frank Herbert", 10.99, 3.50),
        ("Project Hail Mary - Andy Weir", 17.99, 5.00),
        ("Deep Work - Cal Newport", 15.99, 4.50),
        ("Thinking Fast and Slow", 17.00, 5.50),
        ("The Staff Engineer's Path", 49.99, 20.00),
    ],
}

PAYMENT_METHODS = ["visa", "mastercard", "paypal", "amex", "apple_pay", "google_pay", "discover"]
SHIPPING_METHODS = ["standard", "express", "overnight", "free_standard", "store_pickup"]
ORDER_STATUSES = ["completed", "completed", "completed", "shipped", "processing", "refunded", "cancelled"]
DISCOUNT_CODES = ["SAVE10", "SUMMER20", "WELCOME15", "FLASH25", "VIP30", None, None, None, None, None]

US_STATES = ["CA", "TX", "FL", "NY", "PA", "IL", "OH", "GA", "NC", "MI",
             "NJ", "VA", "WA", "AZ", "MA", "TN", "IN", "MO", "MD", "WI"]

def random_date(start_days_ago=730, end_days_ago=0):
    start = datetime.now() - timedelta(days=start_days_ago)
    end = datetime.now() - timedelta(days=end_days_ago)
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))

def realistic_browse_time():
    # people browse at realistic hours
    hour = random.choices(
        range(24),
        weights=[1,1,1,1,1,2,3,5,7,8,9,10,9,8,8,9,10,11,12,10,8,6,4,2],
        k=1
    )[0]
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return hour, minute, second

def build_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # --- schema ---
    c.executescript("""
    CREATE TABLE customers (
        customer_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name      TEXT NOT NULL,
        last_name       TEXT NOT NULL,
        email           TEXT UNIQUE NOT NULL,
        phone           TEXT,
        city            TEXT,
        state           TEXT,
        zip_code        TEXT,
        country         TEXT DEFAULT 'US',
        created_at      DATETIME,
        last_login      DATETIME,
        is_subscribed   INTEGER DEFAULT 1,
        loyalty_points  INTEGER DEFAULT 0
    );

    CREATE TABLE products (
        product_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT NOT NULL,
        category        TEXT NOT NULL,
        price           REAL NOT NULL,
        cost            REAL NOT NULL,
        stock_qty       INTEGER DEFAULT 0,
        sku             TEXT UNIQUE,
        rating          REAL,
        review_count    INTEGER DEFAULT 0,
        is_active       INTEGER DEFAULT 1
    );

    CREATE TABLE orders (
        order_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id     INTEGER NOT NULL,
        order_date      DATETIME NOT NULL,
        status          TEXT NOT NULL,
        subtotal        REAL,
        discount        REAL DEFAULT 0,
        shipping_cost   REAL,
        tax             REAL,
        total           REAL,
        payment_method  TEXT,
        shipping_method TEXT,
        discount_code   TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );

    CREATE TABLE order_items (
        item_id         INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id        INTEGER NOT NULL,
        product_id      INTEGER NOT NULL,
        quantity        INTEGER NOT NULL,
        unit_price      REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );

    CREATE TABLE sessions (
        session_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id     INTEGER,
        session_date    DATETIME,
        duration_secs   INTEGER,
        pages_viewed    INTEGER,
        device_type     TEXT,
        source          TEXT,
        converted       INTEGER DEFAULT 0,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );

    CREATE TABLE reviews (
        review_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id      INTEGER NOT NULL,
        customer_id     INTEGER NOT NULL,
        rating          INTEGER NOT NULL,
        review_text     TEXT,
        created_at      DATETIME,
        helpful_votes   INTEGER DEFAULT 0,
        FOREIGN KEY (product_id) REFERENCES products(product_id),
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );

    CREATE TABLE support_tickets (
        ticket_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id     INTEGER NOT NULL,
        order_id        INTEGER,
        subject         TEXT,
        status          TEXT DEFAULT 'open',
        priority        TEXT DEFAULT 'normal',
        created_at      DATETIME,
        resolved_at     DATETIME,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );
    """)

    # --- customers ---
    print("Generating customers...")
    customer_ids = []
    used_emails = set()
    for _ in range(2000):
        first = fake.first_name()
        last = fake.last_name()
        email_base = f"{first.lower()}.{last.lower()}"
        email = f"{email_base}{random.randint(1,999) if email_base in used_emails else ''}@{random.choice(['gmail.com','yahoo.com','outlook.com','hotmail.com','icloud.com','protonmail.com'])}"
        used_emails.add(email_base)
        created = random_date(730, 30)
        last_login = created + timedelta(days=random.randint(1, 300))
        state = random.choice(US_STATES)
        c.execute("""INSERT INTO customers
            (first_name, last_name, email, phone, city, state, zip_code, created_at, last_login, is_subscribed, loyalty_points)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (first, last, email,
             fake.numerify("(###) ###-####"),
             fake.city(), state,
             fake.zipcode_in_state(state),
             created.strftime("%Y-%m-%d %H:%M:%S"),
             last_login.strftime("%Y-%m-%d %H:%M:%S"),
             random.choices([1, 0], weights=[80, 20])[0],
             random.randint(0, 5000)))
        customer_ids.append(c.lastrowid)

    # --- products ---
    print("Generating products...")
    product_ids = []
    all_products = []
    sku_counter = 10001
    for category, items in CATEGORIES.items():
        for name, price, cost in items:
            rating = round(random.uniform(3.5, 5.0), 1)
            review_count = random.randint(12, 4800)
            stock = random.randint(0, 500)
            c.execute("""INSERT INTO products
                (name, category, price, cost, stock_qty, sku, rating, review_count, is_active)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (name, category, price, cost, stock,
                 f"SKU-{sku_counter}", rating, review_count,
                 random.choices([1, 0], weights=[95, 5])[0]))
            pid = c.lastrowid
            product_ids.append(pid)
            all_products.append((pid, price, category))
            sku_counter += 1

    # --- orders + order_items ---
    print("Generating orders...")
    order_ids = []
    for _ in range(8000):
        cid = random.choice(customer_ids)
        order_date = random_date(720, 0)
        h, m, s = realistic_browse_time()
        order_date = order_date.replace(hour=h, minute=m, second=s)
        status = random.choice(ORDER_STATUSES)
        payment = random.choice(PAYMENT_METHODS)
        shipping_method = random.choice(SHIPPING_METHODS)
        discount_code = random.choice(DISCOUNT_CODES)
        shipping_cost = round(random.choice([0, 0, 4.99, 7.99, 12.99, 19.99]), 2)
        if shipping_method == "free_standard" or shipping_method == "store_pickup":
            shipping_cost = 0.0

        # pick 1-4 items
        num_items = random.choices([1,2,3,4], weights=[50,30,15,5])[0]
        chosen = random.sample(all_products, min(num_items, len(all_products)))
        subtotal = 0
        for pid, price, _ in chosen:
            qty = random.choices([1,2,3], weights=[70,20,10])[0]
            subtotal += round(price * qty, 2)

        discount = 0
        if discount_code == "SAVE10": discount = round(subtotal * 0.10, 2)
        elif discount_code == "SUMMER20": discount = round(subtotal * 0.20, 2)
        elif discount_code == "WELCOME15": discount = round(subtotal * 0.15, 2)
        elif discount_code == "FLASH25": discount = round(subtotal * 0.25, 2)
        elif discount_code == "VIP30": discount = round(subtotal * 0.30, 2)

        tax = round((subtotal - discount) * 0.0875, 2)
        total = round(subtotal - discount + shipping_cost + tax, 2)

        c.execute("""INSERT INTO orders
            (customer_id, order_date, status, subtotal, discount, shipping_cost, tax, total, payment_method, shipping_method, discount_code)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (cid, order_date.strftime("%Y-%m-%d %H:%M:%S"), status,
             subtotal, discount, shipping_cost, tax, total,
             payment, shipping_method, discount_code))
        oid = c.lastrowid
        order_ids.append(oid)

        for pid, price, _ in chosen:
            qty = random.choices([1,2,3], weights=[70,20,10])[0]
            c.execute("INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?,?,?,?)",
                      (oid, pid, qty, price))

    # --- sessions ---
    print("Generating sessions...")
    devices = ["desktop", "mobile", "tablet"]
    sources = ["google", "direct", "email", "instagram", "facebook", "tiktok", "referral", "bing"]
    for _ in range(15000):
        cid = random.choice(customer_ids + [None] * 300)
        sess_date = random_date(365, 0)
        h, m, s = realistic_browse_time()
        sess_date = sess_date.replace(hour=h, minute=m, second=s)
        converted = random.choices([1, 0], weights=[18, 82])[0]
        c.execute("""INSERT INTO sessions
            (customer_id, session_date, duration_secs, pages_viewed, device_type, source, converted)
            VALUES (?,?,?,?,?,?,?)""",
            (cid, sess_date.strftime("%Y-%m-%d %H:%M:%S"),
             random.randint(15, 1800),
             random.randint(1, 24),
             random.choice(devices),
             random.choice(sources),
             converted))

    # --- reviews ---
    print("Generating reviews...")
    review_texts = {
        5: ["Absolutely love this!", "Works exactly as described.", "Would buy again without hesitation.",
            "Super happy with this purchase.", "Exceeded my expectations honestly."],
        4: ["Really good overall, minor issues.", "Good value for the price.", "Happy with it, works well.",
            "Solid product, would recommend.", "Does what it says, pretty satisfied."],
        3: ["It's okay, nothing special.", "Works but had some issues.", "Average product for the price.",
            "Decent but could be better.", "Mixed feelings, some good some bad."],
        2: ["Disappointed with quality.", "Had issues right out of the box.", "Not what I expected at all.",
            "Returning this, not worth it.", "Wouldn't recommend to a friend."],
        1: ["Complete waste of money.", "Broke after one week.", "Terrible quality, very disappointed.",
            "Nothing works as advertised.", "Save your money, skip this one."],
    }
    used_pairs = set()
    for _ in range(5000):
        pid = random.choice(product_ids)
        cid = random.choice(customer_ids)
        if (pid, cid) in used_pairs:
            continue
        used_pairs.add((pid, cid))
        rating = random.choices([5,4,3,2,1], weights=[45,30,13,7,5])[0]
        text = random.choice(review_texts[rating])
        created = random_date(500, 1)
        c.execute("""INSERT INTO reviews (product_id, customer_id, rating, review_text, created_at, helpful_votes)
            VALUES (?,?,?,?,?,?)""",
            (pid, cid, rating, text,
             created.strftime("%Y-%m-%d %H:%M:%S"),
             random.randint(0, 120)))

    # --- support tickets ---
    print("Generating support tickets...")
    subjects = [
        "Order not received", "Wrong item shipped", "Refund request",
        "Item arrived damaged", "Tracking number not working",
        "Cancel my order", "Payment issue", "Account login problem",
        "Missing part from package", "Return label request"
    ]
    priorities = ["low", "normal", "normal", "normal", "high", "urgent"]
    statuses = ["open", "open", "resolved", "resolved", "resolved", "closed"]
    for _ in range(1200):
        cid = random.choice(customer_ids)
        oid = random.choice(order_ids) if random.random() > 0.2 else None
        created = random_date(365, 0)
        status = random.choice(statuses)
        resolved = None
        if status in ("resolved", "closed"):
            resolved = (created + timedelta(hours=random.randint(1, 120))).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""INSERT INTO support_tickets
            (customer_id, order_id, subject, status, priority, created_at, resolved_at)
            VALUES (?,?,?,?,?,?,?)""",
            (cid, oid, random.choice(subjects), status,
             random.choice(priorities),
             created.strftime("%Y-%m-%d %H:%M:%S"), resolved))

    conn.commit()
    conn.close()
    print(f"\nDone! Database saved to: {DB_PATH}")
    print(f"Tables: customers, products, orders, order_items, sessions, reviews, support_tickets")

if __name__ == "__main__":
    build_db()
