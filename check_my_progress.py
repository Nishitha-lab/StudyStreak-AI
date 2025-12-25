import sqlite3

def check_progress():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("--- Checking 'user_progress' table ---")

    # Get ALL progress records for ALL users
    cursor.execute(
        "SELECT id, user_id, quiz_id, ai_quiz_topic, score, total_questions FROM user_progress"
    )
    rows = cursor.fetchall()

    if not rows:
        print("The 'user_progress' table is completely empty.")
        print("This is why your profile is empty. Go take a quiz!")
    else:
        print(f"Found {len(rows)} total records in the table:")
        for row in rows:
            print(dict(row))

    conn.close()

if __name__ == "__main__":
    check_progress()