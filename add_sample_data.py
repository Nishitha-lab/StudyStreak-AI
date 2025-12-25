import sqlite3

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

conn = get_db_connection()

# --- Create a sample quiz ---
try:
    # Insert a quiz and get its new ID
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quizzes (title, subject) VALUES (?, ?)",
                   ('Physics Quiz 1', 'Physics'))
    
    # Get the ID of the quiz we just inserted
    quiz_id = cursor.lastrowid 

    # --- Add questions for this quiz ---
    questions = [
        (quiz_id, 'What is the SI unit of force?', 'Watt', 'Joule', 'Newton', 'Pascal', 'Newton'),
        (quiz_id, 'What is the formula for kinetic energy?', 'mgh', '1/2 mv^2', 'F=ma', 'P=IV', '1/2 mv^2'),
        (quiz_id, 'What does "g" (as in 9.8 m/s^2) stand for?', 'Gravity', 'Gravitational Constant', 'Giga', 'Gravitational Acceleration', 'Gravitational Acceleration')
    ]
    
    conn.executemany(
        'INSERT INTO questions (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_answer) VALUES (?, ?, ?, ?, ?, ?, ?)',
        questions
    )
    
    conn.commit()
    print(f"Successfully added quiz 'Physics Quiz 1' with ID {quiz_id} and 3 questions.")

except sqlite3.IntegrityError:
    print("Sample data might already exist.")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    conn.close()