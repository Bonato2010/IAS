import sqlite3
from pathlib import Path

BASE_PATHS = [
    Path(r"C:\Users\jcvse\OneDrive\Desktop\Daniel\CENTRAL SHORTS"),
    Path(r"C:\Users\jcvse\podcast_cutter")
]

for base in BASE_PATHS:
    schema_file = base / "database/schema.sql"
    db_file = base / "database/shorts_central.db"
    if schema_file.exists():
        with open(schema_file, "r", encoding="utf-8") as f:
            sql = f.read()
        conn = sqlite3.connect(str(db_file))
        conn.executescript(sql)
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        conn.close()
        print(f"[{base.name}] Tables ({len(tables)}): {tables}")
