"""
Simple script to display all records in the environment_logs table of the SQLite database.
Usage:
    python view_logs.py
"""
import sqlite3
import os

DB_PATH = 'thermal_img.db'


def view_all_logs(db_path):
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Retrieve all columns and rows from environment_logs
    cursor.execute("SELECT * FROM environment_logs")
    rows = cursor.fetchall()
    headers = [description[0] for description in cursor.description]

    # Print header
    print(" | ".join(headers))
    print("-" * (len(headers) * 15))

    # Print each log row
    for row in rows:
        print(" | ".join(str(item) for item in row))

    conn.close()


if __name__ == '__main__':
    view_all_logs(DB_PATH)