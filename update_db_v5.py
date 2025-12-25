# update_db_v5.py
import sqlite3

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

conn = get_db_connection()
cursor = conn.cursor()

try:
    # Add the new media_url column to the posts table
    # It can be NULL because not all posts will have media
    cursor.execute("ALTER TABLE posts ADD COLUMN media_url TEXT")
    print("Successfully added 'media_url' column to 'posts' table.")
    conn.commit()
except sqlite3.OperationalError as e:
    # This will probably fail if the column already exists
    print(f"Could not add column: {e}")
finally:
    conn.close()