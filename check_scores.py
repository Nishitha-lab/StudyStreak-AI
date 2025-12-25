import sqlite3
DB='database.db'
USER_ID=1  # change

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute('SELECT id, user_id, quiz_id, ai_quiz_topic, score, total_questions, completed_at FROM user_progress WHERE user_id=? ORDER BY completed_at DESC', (USER_ID,))
rows = cur.fetchall()
print(len(rows), "rows for user", USER_ID)
for r in rows:
    print(dict(r))
conn.close()
