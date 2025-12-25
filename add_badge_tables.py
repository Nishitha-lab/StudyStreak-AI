import sqlite3
from datetime import datetime

def setup_badge_tables():
    """
    Connects to the database and adds the 'badges' 
    and 'user_badges' tables without deleting existing data.
    """
    
    print("Connecting to database.db...")
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # --- 1. Create the 'badges' table ---
    # This stores the master list of all possible badges.
    # We use 'icon' to store the name of a Lucide icon (e.g., 'award', 'star')
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            icon TEXT NOT NULL
        );
        """)
        print("Successfully created 'badges' table (if it didn't exist).")
    except Exception as e:
        print(f"Error creating 'badges' table: {e}")
        conn.close()
        return

    # --- 2. Create the 'user_badges' table ---
    # This table links a user to a badge they have earned.
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            badge_id INTEGER NOT NULL,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (badge_id) REFERENCES badges (id) ON DELETE CASCADE
        );
        """)
        print("Successfully created 'user_badges' table (if it didn't exist).")
    except Exception as e:
        print(f"Error creating 'user_badges' table: {e}")
        conn.close()
        return

    # --- 3. Add some initial badges to the 'badges' table ---
    # We use 'INSERT OR IGNORE' so it doesn't add duplicates if you run it again.
    
    initial_badges = [
        (1, 'First Steps', 'Registered for an account', 'play-circle'),
        (2, 'Quiz Taker', 'Completed your first quiz', 'check-circle'),
        (3, 'Streak Starter', 'Achieved a 3-day study streak', 'flame'),
        (4, 'Community Poster', 'Made your first post in the community', 'message-square'),
        (5, 'Quiz Master', 'Completed 10 quizzes', 'award')
    ]
    
    try:
        cursor.executemany("""
        INSERT OR IGNORE INTO badges (id, name, description, icon) 
        VALUES (?, ?, ?, ?);
        """, initial_badges)
        
        print(f"Inserted/Ignored {len(initial_badges)} initial badges.")
    except Exception as e:
        print(f"Error inserting initial badges: {e}")
    
    # --- 4. Commit changes and close ---
    conn.commit()
    conn.close()
    print("Database setup complete. Tables are ready.")
# --- PASTE THIS NEW FUNCTION INTO SECTION 2 OF app.py ---



# --- Run the function when the script is executed ---
if __name__ == '__main__':
    setup_badge_tables()