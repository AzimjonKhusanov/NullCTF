import sqlite3

db = sqlite3.connect("database.db")

db.execute("""
CREATE TABLE users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT UNIQUE,
password TEXT,
score INTEGER DEFAULT 0
)
""")

db.commit()

print("Database created")