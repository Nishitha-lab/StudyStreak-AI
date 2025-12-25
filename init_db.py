# init_db.py (updated)
import sqlite3

# Connect to (or create) the database file
connection = sqlite3.connect('database.db')
cursor = connection.cursor()

# --- Create 'users' table ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    points INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
''')

# --- Create 'quizzes' table ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    subject TEXT NOT NULL
);
''')

# --- Create 'questions' table ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER,
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
);
''')

# --- Create 'user_progress' table (updated schema) ---
# Supports both static quizzes (quiz_id) and AI quizzes (ai_quiz_topic)
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    quiz_id INTEGER,                      -- nullable: static quiz ID or NULL for AI quizzes
    ai_quiz_topic TEXT DEFAULT NULL,      -- the topic for AI-generated quizzes
    score INTEGER NOT NULL,
    total_questions INTEGER DEFAULT NULL, -- store total questions so profile can show "score/total"
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (quiz_id) REFERENCES quizzes (id)
);
''')

# --- Corrected snippet for defining the 'posts' table structure ---

('posts', """
    CREATE TABLE posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        exam_group TEXT NOT NULL,
        channel TEXT NOT NULL,
        content TEXT NOT NULL,
        media_url TEXT,  -- Column to store the path to uploaded media (images, videos, audio)
        parent_post_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (parent_post_id) REFERENCES posts (id)
    );
""")

# --- Create 'schedule' table ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
''')

connection.commit()
connection.close()

print("Database and tables created successfully (init_db.py).")
