import sqlite3
import os

db_path = "audit_history.db"

if not os.path.exists(db_path):
    print("DB file not found")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(audits)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Columns in 'audits' table: {columns}")
        
        required = ['invoice_header', 'consistency_errors']
        missing = [col for col in required if col not in columns]
        
        if missing:
            print(f"MISSING COLUMNS: {missing}")
        else:
            print("SCHEMA OK")
    except Exception as e:
        print(f"Error reading DB: {e}")
    finally:
        conn.close()
