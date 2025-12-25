import sqlite3

def fix_data():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("Searching for old quiz records...")

    # Find all static quiz records (where quiz_id is not null)
    # that are missing the total_questions data.
    cursor.execute(
        "SELECT id, quiz_id FROM user_progress WHERE quiz_id IS NOT NULL AND total_questions IS NULL"
    )
    rows_to_fix = cursor.fetchall()

    if not rows_to_fix:
        print("No old quiz records found to fix. Your database is all good.")
        conn.close()
        return

    print(f"Found {len(rows_to_fix)} old quiz records to update...")

    for row in rows_to_fix:
        progress_id = row['id']
        quiz_id = row['quiz_id']

        # Now, for this quiz_id, count how many questions it *actually* has
        cursor.execute("SELECT COUNT(id) AS total FROM questions WHERE quiz_id = ?", (quiz_id,))
        count_result = cursor.fetchone()

        if count_result and count_result['total'] > 0:
            total = count_result['total']
            print(f"Fixing progress record {progress_id} (Quiz ID: {quiz_id}). Setting total_questions to {total}.")

            # Update the row with the correct total
            cursor.execute(
                "UPDATE user_progress SET total_questions = ? WHERE id = ?",
                (total, progress_id)
            )
        else:
            print(f"Skipping progress record {progress_id}. Could not find questions for quiz_id {quiz_id}.")

    conn.commit()
    conn.close()
    print("Database backfill complete!")

if __name__ == "__main__":
    fix_data()