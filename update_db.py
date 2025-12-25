# update_db.py
import sqlite3

DB = "database.db"

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns

def main():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    print("🔍 Checking user_progress table...")

    # If table doesn't exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_progress'")
    if not cursor.fetchone():
        print("❌ user_progress table does NOT exist. Nothing to update.")
        conn.close()
        return

    # ---- FIX 1: Make quiz_id nullable (SQLite cannot modify directly) ----
    # We check if table needs rebuild
    cursor.execute("PRAGMA table_info(user_progress)")
    table_info = cursor.fetchall()
    quiz_id_not_nullable = any(col[1] == "quiz_id" and col[3] == 1 for col in table_info)

    # ---- FIX 2 & 3: Check missing columns ----
    needs_ai_topic = not column_exists(cursor, "user_progress", "ai_quiz_topic")
    needs_total_q = not column_exists(cursor, "user_progress", "total_questions")

    # If nothing to fix
    if not quiz_id_not_nullable and not needs_ai_topic and not needs_total_q:
        print("✔ Database is already updated. No changes needed.")
        conn.close()
        return

    print("⚠ Updating user_progress table...")

    # 1. Rename old table
    cursor.execute("ALTER TABLE user_progress RENAME TO user_progress_old;")

    # 2. Create new table with correct schema
    cursor.execute('''
        CREATE TABLE user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            quiz_id INTEGER,                     -- now nullable
            ai_quiz_topic TEXT DEFAULT NULL,     -- for AI quizzes
            score INTEGER NOT NULL,
            total_questions INTEGER DEFAULT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
        );
    ''')

    # 3. Copy over EXISTING data
    cursor.execute('''
        INSERT INTO user_progress (id, user_id, quiz_id, score, completed_at)
        SELECT id, user_id, quiz_id, score, completed_at
        FROM user_progress_old;
    ''')

    # 4. Drop old table
    cursor.execute("DROP TABLE user_progress_old;")

    conn.commit()
    conn.close()

    print("🎉 Update complete! user_progress table is now fully compatible with AI quiz scores.")

if __name__ == "__main__":
    main()
