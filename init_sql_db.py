import sqlite3
import os

# Optional: Define where to save the database
db_path = "thermal_img.db"

# Connect to or create the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Enable foreign key constraints
cursor.execute("PRAGMA foreign_keys = ON")

# Create the static info table: static
cursor.execute("""
CREATE TABLE IF NOT EXISTS static (
    location_id TEXT PRIMARY KEY,
    building_name TEXT,
    floor_number INTEGER,
    side_of_building TEXT
)
""")

# Create the dynamic info table: environment_logs
cursor.execute("""
CREATE TABLE IF NOT EXISTS environment_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id TEXT,
    outside_temp REAL,
    min_temp REAL,
    max_temp REAL,
    time_taken_hours INTEGER,
    windows_opened TEXT CHECK(windows_opened IN ('Y', 'N')),
    date TEXT,
    url TEXT,
    FOREIGN KEY (location_id) REFERENCES static(location_id)
)
""")

# Commit and close the connection
conn.commit()
conn.close()

print(f"Database initialized at: {os.path.abspath(db_path)}")
