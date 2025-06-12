import sqlite3
import os
from config import DATABASE, UPLOAD_FOLDER

def connect_db():
    return sqlite3.connect(DATABASE, timeout=10)

def create_tables():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS photos (
                photo_id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT UNIQUE,
                votes INTEGER DEFAULT 0
            )""")
        conn.commit()

def initialize_photos_from_folder():
    files = os.listdir(UPLOAD_FOLDER)
    with connect_db() as conn:
        cursor = conn.cursor()
        for file in files:
            cursor.execute(
                "INSERT OR IGNORE INTO photos (file_name) VALUES (?)",
                (file,))
        conn.commit()

def add_photo(file_name):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO photos (file_name) VALUES (?)",
            (file_name,))
        conn.commit()

def get_two_random_photos():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT file_name FROM photos ORDER BY RANDOM() LIMIT 2")
        return [row[0] for row in cursor.fetchall()]

def vote_photo(file_name):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE photos SET votes = votes + 1 WHERE file_name = ?",
            (file_name,))
        conn.commit()

def get_top_photos():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_name, votes FROM photos ORDER BY votes DESC LIMIT 10")
        return cursor.fetchall()
