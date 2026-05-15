import sqlite3
import os

DB_FILE = "tablet_order.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Products Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            price INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            image_url TEXT
        )
    ''')
    
    # Orders Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            contact TEXT NOT NULL,
            address TEXT NOT NULL,
            memo TEXT,
            status TEXT DEFAULT 'pending', -- pending, exported
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Order Items Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')
    
    # Settings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            sender_name TEXT,
            sender_email TEXT,
            sender_password TEXT,
            receiver_name TEXT,
            receiver_email TEXT,
            cc_name TEXT,
            cc_email TEXT
        )
    ''')
    
    # Insert default settings if empty
    cursor.execute('SELECT COUNT(*) FROM settings')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO settings (id, sender_name, sender_email, sender_password, receiver_name, receiver_email, cc_name, cc_email)
            VALUES (1, '영업팀', '', '', '물류팀', '', '', '')
        ''')
    
    # Insert default products if table is empty
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        default_products = [
            ("WK1209", "(본품)위칙파워효소액체세제(1.5L)(표시변경)"),
            ("WK1114", "(본품)위칙소독섬유유연제(2L)(신형라벨)"),
            ("WK1103", "(본품)위칙소독섬유유연제(리필)(1.7L)"),
            ("WK1306", "(본품)위칙이염방지시트(30매)(new)"),
            ("WK1307", "(본품)위칙건조기시트(30매)"),
            ("WK1210", "멀티플 주방세제(500ml)"),
            ("WK1211", "멀티플 주방세제(1L)"),
            ("WK1401", "파워 솔트 식기세척기 타블렛(60개입)"),
            ("WK1501", "차량용 세정티슈(70매)"),
            ("WK1502", "멀티 세정티슈(180매)"),
            ("WK1601", "멀티소독스프레이(500ml)"),
            ("WK1602", "소독 섬유탈취제(500ml)")
        ]
        cursor.executemany('INSERT INTO products (code, name) VALUES (?, ?)', default_products)
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
