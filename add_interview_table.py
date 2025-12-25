import sqlite3

def setup_interview_table():
    """
    Connects to the database and adds the 'interviews' table.
    """
    
    print("Connecting to database.db...")
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            transcript TEXT NOT NULL,
            score_confidence INTEGER,
            score_clarity INTEGER,
            feedback TEXT,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
        """)
        print("Successfully created 'interviews' table (if it didn't exist).")
    except Exception as e:
        print(f"Error creating 'interviews' table: {e}")
    finally:
        conn.commit()
        conn.close()
        print("Database setup complete.")

# --- Run the function when the script is executed ---
if __name__ == '__main__':
    setup_interview_table()