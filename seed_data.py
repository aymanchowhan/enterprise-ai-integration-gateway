import random
from db import get_conn, init_db

random.seed(42)  # same data every run
init_db()

COUNTRIES = ["USA", "Germany", "India", "UAE", "UK", "Japan", "Brazil", "Canada"]
STATUSES = ["Pending Approval", "Approved", "Rejected"]
NAMES = [
    "Nova Metals", "BlueWave Logistics", "Summit Tools", "Orion Packaging",
    "Delta Chemicals", "Falcon Electronics", "Harbor Freight Co", "Pioneer Plastics",
    "Sterling Steel", "Zenith Textiles", "Atlas Machinery", "Crescent Foods",
    "Vertex Software", "Lotus Paper", "Ironbridge Parts", "Meridian Oils", "Skyline Glass",
]

# Keep your original rows first so your tests still pass
vendors = [
    ("V-001", "Acme Supplies", "USA", 4.2),
    ("V-002", "Globex Corp", "Germany", 3.8),
    ("V-003", "Initech", "India", 4.5),
]
for i, name in enumerate(NAMES, start=4):
    vendors.append((f"V-{i:03d}", name, random.choice(COUNTRIES), round(random.uniform(2.5, 5.0), 1)))

orders = [
    ("PO-1001", "V-001", "Acme Supplies", 15000, "Pending Approval"),
    ("PO-1002", "V-002", "Globex Corp", 4200, "Approved"),
    ("PO-1003", "V-003", "Initech", 32000, "Pending Approval"),
    ("PO-1004", "V-001", "Acme Supplies", 8700, "Approved"),
    ("PO-1005", "V-002", "Globex Corp", 21000, "Rejected"),
]
for n in range(1006, 1201):
    v = random.choice(vendors)
    orders.append((f"PO-{n}", v[0], v[1], random.randint(500, 50000), random.choice(STATUSES)))

with get_conn() as conn:
    conn.execute("DELETE FROM vendors")
    conn.execute("DELETE FROM purchase_orders")
    conn.executemany("INSERT INTO vendors VALUES (?,?,?,?)", vendors)
    conn.executemany("INSERT INTO purchase_orders VALUES (?,?,?,?,?)", orders)

print(f"Loaded {len(vendors)} vendors and {len(orders)} purchase orders")