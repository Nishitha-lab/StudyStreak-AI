import sqlite3

def fix_table():
    print("Connecting to database.db to add 'strengths' column...")
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    try:
        # Add the 'strengths' column to the 'interviews' table
        cursor.execute("ALTER TABLE interviews ADD COLUMN strengths TEXT")
        print("Successfully added 'strengths' column to 'interviews' table.")
    except sqlite3.OperationalError as e:
        # This error happens if the column already exists, which is fine
        if "duplicate column name" in str(e):
            print("Column 'strengths' already exists. No changes made.")
        else:
            print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An unknown error occurred: {e}")
    finally:
        conn.commit()
        conn.close()
        print("Database fix complete.")

if __name__ == '__main__':
    fix_table()