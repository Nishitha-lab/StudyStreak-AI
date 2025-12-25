import sqlite3

def update_database_v4():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # --- 1. Add 'parent_post_id' to the 'posts' table ---
    try:
        cursor.execute('''
        ALTER TABLE posts
        ADD COLUMN parent_post_id INTEGER DEFAULT NULL
        ''')
        print("Successfully added 'parent_post_id' column to 'posts' table.")
    except sqlite3.OperationalError as e:
        print(f"Info (posts): {e} (This is normal if the column already exists)")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    update_database_v4()