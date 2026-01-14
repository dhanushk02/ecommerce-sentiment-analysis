import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.executescript("""
CREATE TABLE IF NOT EXISTS tblusers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tbladminlogin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    userid TEXT,
    password TEXT
);

CREATE TABLE IF NOT EXISTS tblcategories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Category TEXT
);

CREATE TABLE IF NOT EXISTS tblproducts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price REAL,
    category_id INTEGER,
    description TEXT,
    image TEXT
);

CREATE TABLE IF NOT EXISTS tblorders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    address TEXT,
    status TEXT,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tblreviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    user_id INTEGER,
    review_text TEXT,
    sentiment TEXT,
    emotion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

conn.commit()
conn.close()
print("Database created")
