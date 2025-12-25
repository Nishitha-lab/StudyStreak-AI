import sqlite3

def update_database_v3():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # --- 1. Add 'exam_group' to the 'users' table ---
    try:
        cursor.execute('''
        ALTER TABLE users
        ADD COLUMN exam_group TEXT DEFAULT NULL
        ''')
        print("Successfully added 'exam_group' column to 'users' table.")
    except sqlite3.OperationalError as e:
        print(f"Info (users): {e} (This is normal if the column already exists)")

    # --- 2. Rebuild the 'posts' table (This will delete old posts) ---
    try:
        cursor.execute('DROP TABLE IF EXISTS posts;')
        print("Dropped old 'posts' table.")

        cursor.execute('''
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exam_group TEXT NOT NULL,
            channel TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        ''')
        print("Successfully created new 'posts' table with 'exam_group' and 'channel' columns.")
    except Exception as e:
        print(f"An error occurred while rebuilding 'posts' table: {e}")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    update_database_v3()