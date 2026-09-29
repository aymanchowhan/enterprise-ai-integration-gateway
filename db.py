import sqlite3

DB_PATH = "gateway.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS vendors (
            vendor_id TEXT PRIMARY KEY, name TEXT, country TEXT, rating REAL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS purchase_orders (
            po_id TEXT PRIMARY KEY, vendor_id TEXT, vendor TEXT, amount REAL, status TEXT)""")

        # Fill with the original sample rows only the first time
        if conn.execute("SELECT COUNT(*) FROM vendors").fetchone()[0] == 0:
            conn.executemany("INSERT INTO vendors VALUES (?,?,?,?)", [
                ("V-001", "Acme Supplies", "USA", 4.2),
                ("V-002", "Globex Corp", "Germany", 3.8),
                ("V-003", "Initech", "India", 4.5),
            ])
            conn.executemany("INSERT INTO purchase_orders VALUES (?,?,?,?,?)", [
                ("PO-1001", "V-001", "Acme Supplies", 15000, "Pending Approval"),
                ("PO-1002", "V-002", "Globex Corp", 4200, "Approved"),
                ("PO-1003", "V-003", "Initech", 32000, "Pending Approval"),
                ("PO-1004", "V-001", "Acme Supplies", 8700, "Approved"),
                ("PO-1005", "V-002", "Globex Corp", 21000, "Rejected"),
            ])

def load_vendors() -> dict:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM vendors").fetchall()
    return {r["vendor_id"]: {"name": r["name"], "country": r["country"], "rating": r["rating"]} for r in rows}

def load_purchase_orders() -> dict:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM purchase_orders").fetchall()
    return {r["po_id"]: {"vendor_id": r["vendor_id"], "vendor": r["vendor"],
                         "amount": r["amount"], "status": r["status"]} for r in rows}