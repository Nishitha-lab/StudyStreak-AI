import sqlite3

def update_tables_v2():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    try:
        # Add 'is_complete' column to the 'schedule' table
        cursor.execute('''
        ALTER TABLE schedule
        ADD COLUMN is_complete INTEGER DEFAULT 0
        ''')
        print("Successfully added 'is_complete' column to 'schedule' table.")
    except sqlite3.OperationalError as e:
        print(f"Info (schedule): {e} (This is normal if the column already exists)")

    try:
        # Add 'current_streak' column to the 'users' table
        cursor.execute('''
        ALTER TABLE users
        ADD COLUMN current_streak INTEGER DEFAULT 0
        ''')
        print("Successfully added 'current_streak' column to 'users' table.")
    except sqlite3.OperationalError as e:
        print(f"Info (users): {e} (This is normal if the column already exists)")

    try:
        # Add 'last_activity_date' column to the 'users' table
        cursor.execute('''
        ALTER TABLE users
        ADD COLUMN last_activity_date TEXT DEFAULT NULL
        ''')
        print("Successfully added 'last_activity_date' column to 'users' table.")
    except sqlite3.OperationalError as e:
        print(f"Info (users): {e} (This is normal if the column already exists)")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    update_tables_v2()