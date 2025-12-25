import sqlite3
import os
import random
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
# Assuming 'ai_helper' module exists and provides required functions
import ai_helper 
from datetime import datetime, date, timedelta

# ----------------------------------------------------------------------
# 1. Configuration and Initialization
# ----------------------------------------------------------------------

app = Flask(__name__)
# IMPORTANT: Change this key in a production environment!
app.secret_key = 'your_super_secret_key' 

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'} 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- External Links Configuration (PYQ) ---
PYQ_LINKS = {
    "JEE": [
        {"title": "JEE Main Official Papers (NTA)", "url": "https://nta.ac.in/Downloads"},
        {"title": "JEE Advanced Official Papers", "url": "https://jeeadv.ac.in/archive.html"}
    ],
    "NEET": [
        {"title": "NEET (UG) Official Portal", "url": "https://exams.nta.ac.in/NEET/"},
        {"title": "NTA Exam Downloads", "url": "https://nta.ac.in/Downloads"}
    ],
    "UPSC": [
        {"title": "UPSC Official Previous Papers", "url": "https://upsc.gov.in/question-papers-listing"},
    ],
    "SSC": [
        {"title": "SSC Official Question Papers", "url": "https://ssc.gov.in/home"}
    ],
    "Other": [
        {"title": "Practice our General Quizzes", "url": "/quizzes"} 
    ]
}

# ----------------------------------------------------------------------
# 2. Helper Functions and Decorators
# ----------------------------------------------------------------------

def get_db_connection():
    """Helper function to create a database connection."""
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    """Checks if a filename has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    """Decorator to protect routes requiring user login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You must be logged in to view this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def calculate_profile_stats(user_id, filter_period='all'):
    """Fetches and calculates user performance stats for the profile page."""
    conn = get_db_connection()
    base_sql = "SELECT q.title, p.score, p.completed_at, p.ai_quiz_topic, p.total_questions, q.subject FROM user_progress p LEFT JOIN quizzes q ON p.quiz_id = q.id WHERE p.user_id = ?"
    params = [user_id]
    
    if filter_period == 'today':
        base_sql += " AND DATE(p.completed_at) = DATE('now')"
    elif filter_period == 'week':
        base_sql += " AND p.completed_at >= DATE('now', '-7 days')"
    elif filter_period == 'month':
        base_sql += " AND p.completed_at >= DATE('now', '-30 days')"
        
    base_sql += " ORDER BY p.completed_at DESC"
    
    progress_rows = conn.execute(base_sql, params).fetchall()
    conn.close()
    
    total_quizzes_taken = len(progress_rows)
    overall_average = 0
    temp_subject_data = {}
    history = []
    
    if total_quizzes_taken > 0:
        total_score_sum = 0
        total_possible_sum = 0
        
        for row in progress_rows:
            item = dict(row)
            item['completed_at_formatted'] = datetime.strptime(item['completed_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M')
            history.append(item)
            
            if (row['total_questions'] or 0) > 0:
                total_score_sum += row['score'] or 0
                total_possible_sum += row['total_questions'] or 0
                
            if row['subject']:
                subject = row['subject']
                if subject not in temp_subject_data:
                    temp_subject_data[subject] = {'score': 0, 'total': 0, 'count': 0}
                temp_subject_data[subject]['score'] += row['score'] or 0
                temp_subject_data[subject]['total'] += row['total_questions'] or 0
                temp_subject_data[subject]['count'] += 1
                
        if total_possible_sum > 0:
            overall_average = int((total_score_sum / total_possible_sum) * 100)
            
    lagging_area = "N/A"
    lowest_avg = 101
    subject_stats = {}
    subject_labels = []
    subject_data = []
    
    for subject, data in temp_subject_data.items():
        if data['total'] > 0:
            average = round((data['score'] / data['total']) * 100)
            subject_stats[subject] = {'average': average, 'count': data['count']}
            subject_labels.append(subject)
            subject_data.append(average)
            if average < lowest_avg:
                lowest_avg = average
                lagging_area = subject
        else:
            subject_stats[subject] = {'average': 0, 'count': 0}
            
    history_text = ""
    for item in history: 
        quiz_name = item.get("ai_quiz_topic") or item.get("title") or "Quiz"
        score = item.get("score", 0)
        total = item.get("total_questions", 10)
        date = item.get("completed_at_formatted", "Unknown Date")
        history_text += f"{quiz_name} – {score}/{total} on {date}\n"
        
    if not history_text:
        history_text = "No quizzes taken for this period."
        
    ai_feedback = ai_helper.get_ai_coach_feedback(history_text)
    
    return {
        "total_quizzes_taken": total_quizzes_taken,
        "overall_average": overall_average,
        "subject_stats": subject_stats,
        "subject_labels": subject_labels,
        "subject_data": subject_data,
        "lagging_area": lagging_area,
        "ai_feedback": ai_feedback,
        "history": history
    }


def award_badge(user_id, badge_name):
    """
    Awards a badge to a user by its name, if they don't already have it.
    Flashes a success message.
    """
    conn = get_db_connection()
    try:
        # 1. Find the badge ID from its name
        badge = conn.execute('SELECT id, icon, description FROM badges WHERE name = ?', (badge_name,)).fetchone()
        
        if not badge:
            print(f"Warning: A badge with the name '{badge_name}' was not found in the database.")
            conn.close()
            return

        badge_id = badge['id']
        
        # 2. Check if the user already has this badge
        exists = conn.execute(
            'SELECT 1 FROM user_badges WHERE user_id = ? AND badge_id = ?', 
            (user_id, badge_id)
        ).fetchone()
        
        # 3. If they don't have it, insert it
        if not exists:
            conn.execute(
                'INSERT INTO user_badges (user_id, badge_id) VALUES (?, ?)',
                (user_id, badge_id)
            )
            conn.commit()
            
            # 4. Flash a message to the user!
            flash_message = f"Badge Earned: {badge_name}! {badge['description']}"
            flash(flash_message, 'success')
            print(f"Awarded badge '{badge_name}' to user {user_id}")
            
    except Exception as e:
        print(f"Error awarding badge: {e}")
        conn.rollback() # Roll back any changes if an error occurs
    finally:
        conn.close()

def check_quiz_badges(user_id):
    """
    Checks for quiz-related badges after a quiz is completed.
    This runs separately to not interfere with route-specific connections.
    """
    conn = get_db_connection()
    try:
        # Get total number of quizzes taken
        quiz_count_row = conn.execute(
            'SELECT COUNT(*) FROM user_progress WHERE user_id = ?', 
            (user_id,)
        ).fetchone()
        
        quiz_count = quiz_count_row[0] if quiz_count_row else 0
        
        # Award 'Quiz Taker' (first quiz)
        if quiz_count >= 1:
            award_badge(user_id, 'Quiz Taker')
            
        # Award 'Quiz Master' (10 quizzes)
        if quiz_count >= 10:
            award_badge(user_id, 'Quiz Master')
            
    except Exception as e:
        print(f"Error checking quiz badges: {e}")
    finally:
        conn.close()

def get_confidence_heatmap(user_id):
    """
    Calculates the user's average score for every AI quiz topic.
    Returns a list of topics and their confidence score (0-100).
    """
    conn = get_db_connection()
    heatmap_data = []
    try:
        query = """
        SELECT
            ai_quiz_topic,
            SUM(score) AS total_scored,
            SUM(total_questions) AS total_possible,
            (SUM(score) * 100.0 / SUM(total_questions)) AS confidence
        FROM user_progress
        WHERE user_id = ? AND ai_quiz_topic IS NOT NULL
        GROUP BY ai_quiz_topic
        ORDER BY confidence DESC
        """
        rows = conn.execute(query, (user_id,)).fetchall()
        
        for row in rows:
            heatmap_data.append(dict(row))
            
    except Exception as e:
        print(f"Error generating heatmap: {e}")
    finally:
        conn.close()
        
    return heatmap_data

# ----------------------------------------------------------------------
# 3. Authentication Routes
# ----------------------------------------------------------------------

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        exam_group = request.form['exam_group']
        hashed_password = generate_password_hash(password)
        
        try:
            conn = get_db_connection()
            cursor = conn.execute(
                'INSERT INTO users (username, email, password_hash, exam_group) VALUES (?, ?, ?, ?)',
                (username, email, hashed_password, exam_group)
            )
            conn.commit()
            
            # Award 'First Steps' badge
            new_user_id = cursor.lastrowid 
            award_badge(new_user_id, 'First Steps') 

            conn.close()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('register'))
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['exam_group'] = user['exam_group'] 
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard')) 
        else:
            flash('Incorrect username or password.', 'danger')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ----------------------------------------------------------------------
# 4. Main Feature Routes (Dashboard, Quiz, AI, Community, Schedule)
# ----------------------------------------------------------------------

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    user_row = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    if user_row is None:
        conn.close()
        return redirect(url_for('logout'))
        
    user = dict(user_row)
    
    # --- Streak Check and Update ---
    today_str = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()
    last_activity_date = user.get('last_activity_date')
    current_streak = user.get('current_streak', 0)
    
    heatmap_data = get_confidence_heatmap(session['user_id'])

    # Reset streak if the last activity was before yesterday
    if last_activity_date != today_str and last_activity_date != yesterday_str:
        if current_streak > 0:
            conn.execute('UPDATE users SET current_streak = 0 WHERE id = ?', (session['user_id'],))
            conn.commit()
        current_streak = 0
    
    # --- Dashboard Content Logic ---
    today_iso = date.today().isoformat()
    today_events_rows = conn.execute(
        'SELECT id, title, is_complete FROM schedule WHERE user_id = ? AND DATE(start_time) = ?',
        (session['user_id'], today_iso)
    ).fetchall()
    today_events = [dict(row) for row in today_events_rows]
    total_tasks = len(today_events)
    completed_tasks = sum(1 for task in today_events if task['is_complete'])
    progress_percent = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
    
    all_progress_rows = conn.execute(
        'SELECT score, total_questions, completed_at FROM user_progress WHERE user_id = ? ORDER BY completed_at ASC',
        (session['user_id'],)
    ).fetchall()
    
    total_quizzes_taken = len(all_progress_rows)
    overall_average = 0
    chart_labels = []
    chart_data = []
    
    if total_quizzes_taken > 0:
        total_score_sum = 0
        total_possible_sum = 0
        for row in all_progress_rows:
            if (row['total_questions'] or 0) > 0:
                total_score_sum += row['score'] or 0
                total_possible_sum += row['total_questions'] or 0
                
                percent = round(((row['score'] or 0) / row['total_questions']) * 100)
                chart_data.append(percent)
                date_obj = datetime.strptime(row['completed_at'], '%Y-%m-%d %H:%M:%S')
                chart_labels.append(date_obj.strftime('%b %d'))
                
        if total_possible_sum > 0:
            overall_average = int((total_score_sum / total_possible_sum) * 100)
            
    chart_labels = chart_labels[-10:]
    chart_data = chart_data[-10:]
    
    subject_progress_rows = conn.execute(
        'SELECT p.score, p.total_questions, q.subject FROM user_progress p JOIN quizzes q ON p.quiz_id = q.id WHERE p.user_id = ? AND p.quiz_id IS NOT NULL',
        (session['user_id'],)
    ).fetchall()
    
    temp_subject_data = {}
    for row in subject_progress_rows:
        subject = row['subject']
        if subject not in temp_subject_data:
            temp_subject_data[subject] = {'score': 0, 'total': 0, 'count': 0}
        temp_subject_data[subject]['score'] += row['score'] or 0
        temp_subject_data[subject]['total'] += row['total_questions'] or 0
        temp_subject_data[subject]['count'] += 1
        
    lagging_area = "N/A"
    lowest_avg = 101
    subject_stats = {}
    subject_labels = []
    subject_data = []
    
    for subject, data in temp_subject_data.items():
        if data['total'] > 0:
            average = round((data['score'] / data['total']) * 100)
            subject_stats[subject] = {'average': average, 'count': data['count']}
            subject_labels.append(subject)
            subject_data.append(average)
            
            if average < lowest_avg:
                lowest_avg = average
                lagging_area = subject
        else:
             subject_stats[subject] = {'average': 0, 'count': 0}
             
    # AI Feedback for Dashboard (based on trend)
    trend_summary = f"User's overall average is {overall_average}%.\n"
    trend_summary += "Here are their recent quiz scores (performance trend):\n"
    if not chart_data:
        trend_summary += "No quizzes have been completed yet."
    else:
        recent_scores = [f"On {label}, score was {score}%" for label, score in zip(chart_labels, chart_data)]
        trend_summary += "\n".join(recent_scores)
        
    ai_feedback = ai_helper.get_ai_coach_feedback(trend_summary)
    
    exam_group = session.get('exam_group', 'Other')
    pyq_links = PYQ_LINKS.get(exam_group, PYQ_LINKS['Other'])
    
    conn.close() 
    
    return render_template('dashboard.html', 
        user=user, 
        current_streak=current_streak, 
        today_events=today_events, 
        progress_percent=progress_percent, 
        total_quizzes_taken=total_quizzes_taken, 
        overall_average=overall_average, 
        chart_labels=chart_labels, 
        chart_data=chart_data, 
        subject_stats=subject_stats, 
        subject_labels=subject_labels, 
        subject_data=subject_data, 
        lagging_area=lagging_area, 
        ai_feedback=ai_feedback, 
        pyq_links=pyq_links,
        heatmap_data=heatmap_data
    )

# --- Quiz Routes ---

@app.route('/quizzes')
@login_required
def quiz_list():
    conn = get_db_connection()
    quizzes = conn.execute('SELECT * FROM quizzes').fetchall()
    conn.close()
    return render_template('quiz_list.html', quizzes=quizzes)

@app.route('/quiz/<int:quiz_id>')
@login_required
def quiz(quiz_id):
    conn = get_db_connection()
    quiz = conn.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    questions = conn.execute('SELECT * FROM questions WHERE quiz_id = ?', (quiz_id,)).fetchall()
    conn.close()
    if quiz is None:
        flash('Quiz not found.', 'danger')
        return redirect(url_for('quiz_list'))
    return render_template('quiz.html', quiz=quiz, questions=questions)

@app.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    conn = get_db_connection()
    quiz = conn.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    if quiz is None:
        flash('Quiz not found.', 'danger')
        conn.close()
        return redirect(url_for('quiz_list'))
        
    questions = conn.execute('SELECT * FROM questions WHERE quiz_id = ?', (quiz_id,)).fetchall()
    score = 0
    total_questions = len(questions)
    results = []
    
    for question in questions:
        submitted_answer = request.form.get(f"question_{question['id']}") 
        is_correct = (submitted_answer == question['correct_answer'])
        
        if is_correct:
            score += 1
        
        results.append({
            'question_text': question['question_text'],
            'submitted_answer': submitted_answer,
            'correct_answer': question['correct_answer'],
            'is_correct': is_correct
        })
        
    points_awarded = score * 10
    
    try:
        conn.execute(
            'INSERT INTO user_progress (user_id, quiz_id, score, total_questions) VALUES (?, ?, ?, ?)',
            (session['user_id'], quiz_id, score, total_questions)
        )
        conn.execute(
            'UPDATE users SET points = points + ? WHERE id = ?',
            (points_awarded, session['user_id'])
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f'An error occurred while saving your score: {e}', 'danger')
    finally:
        conn.close()
        
    flash(f'Quiz submitted! You scored {score} out of {total_questions} and earned {points_awarded} points!', 'success')
    
    # Check for quiz badges
    check_quiz_badges(session['user_id'])
    
    return render_template('quiz_results.html', quiz=quiz, results=results, score=score, total_questions=total_questions)


# --- AI Tool Routes ---

@app.route('/ai_tools')
@login_required
def ai_tools():
    return render_template('ai_tools.html')

@app.route('/api/ask_doubt', methods=['POST'])
@login_required
def api_ask_doubt():
    data = request.get_json()
    if 'question' not in data:
        return jsonify({"error": "No question provided."}), 400
    question = data['question']
    answer = ai_helper.get_ai_doubt_response(question)
    return jsonify({"answer": answer})

@app.route('/api/generate_notes', methods=['POST'])
@login_required
def api_generate_notes():
    data = request.get_json()
    if 'topic' not in data:
        return jsonify({"error": "No topic text provided."}), 400
    topic_text = data['topic']
    notes = ai_helper.generate_ai_notes(topic_text)
    return jsonify({"notes": notes})

@app.route('/quiz_generator')
@login_required
def quiz_generator():
    return render_template('quiz_generator.html')

@app.route('/api/generate_quiz', methods=['POST'])
@login_required
def api_generate_quiz():
    data = request.get_json()
    if not data or 'topic' not in data or 'num_questions' not in data:
        return jsonify({"error": "Missing topic or number of questions."}), 400
        
    topic = data['topic']
    
    # --- *** THIS IS THE FIX *** ---
    # Convert num_questions from a string (e.g., "5") to an integer (e.g., 5)
    try:
        num_questions = int(data.get('num_questions', 5))
    except ValueError:
        num_questions = 5 # Default to 5 if conversion fails
    # --- *** END OF FIX *** ---

    difficulty = data.get('difficulty', 'Medium') 
    
    is_late_night = data.get('is_late_night', False) 
    is_distracted = data.get('is_distracted', False)
    
    quiz_data = ai_helper.generate_ai_quiz(
        topic, 
        num_questions, 
        difficulty, 
        is_late_night,
        is_distracted
    )
    
    if "error" in quiz_data:
        return jsonify(quiz_data), 500
        
    return jsonify(quiz_data)

@app.route('/api/save_ai_quiz_score', methods=['POST'])
@login_required
def save_ai_quiz_score():
    data = request.get_json()
    if not data or 'topic' not in data or 'score' not in data or 'total' not in data:
        return jsonify({"status": "error", "message": "Missing data."}), 400
    try:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO user_progress (user_id, ai_quiz_topic, score, total_questions) VALUES (?, ?, ?, ?)',
            (session['user_id'], data['topic'], data['score'], data['total'])
        )
        conn.commit()
        conn.close()
        
        # Check for quiz badges
        check_quiz_badges(session['user_id'])
        
        return jsonify({"status": "success", "message": "Score saved."})
    except Exception as e:
        conn.rollback()
        conn.close()
        
        check_quiz_badges(session['user_id']) 
        
        return jsonify({"status": "error", "message": str(e)}), 500


# --- Schedule Routes ---

@app.route('/schedule')
@login_required
def schedule():
    return render_template('schedule.html')

@app.route('/api/get_events')
@login_required
def get_events():
    conn = get_db_connection()
    events_rows = conn.execute(
        'SELECT id, title, start_time AS start, end_time AS end, is_complete FROM schedule WHERE user_id = ?',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    events = [dict(row) for row in events_rows]
    return jsonify(events)

@app.route('/api/add_event', methods=['POST'])
@login_required
def add_event():
    data = request.get_json()
    if not data or 'title' not in data or 'start' not in data:
        return jsonify({"status": "error", "message": "Missing title or start date"}), 400
    try:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO schedule (user_id, title, start_time, end_time) VALUES (?, ?, ?, ?)',
            (session['user_id'], data['title'], data['start'], data.get('end'))
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Event added successfully"})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/delete_event', methods=['POST'])
@login_required
def delete_event():
    data = request.get_json()
    if not data or 'id' not in data:
        return jsonify({"status": "error", "message": "Invalid data, missing event ID."}), 400
    try:
        conn = get_db_connection()
        result = conn.execute(
            'DELETE FROM schedule WHERE id = ? AND user_id = ?',
            (data['id'], session['user_id'])
        )
        conn.commit()
        conn.close()
        if result.rowcount == 0:
            return jsonify({"status": "error", "message": "Event not found or permission denied."}), 404
        else:
            return jsonify({"status": "success", "message": "Event deleted."})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500
        
@app.route('/api/toggle_task', methods=['POST'])
@login_required
def toggle_task():
    data = request.get_json()
    if 'task_id' not in data or 'is_complete' not in data:
        return jsonify({"status": "error", "message": "Invalid data."}), 400
    task_id = data['task_id']
    is_complete = data['is_complete']
    conn = get_db_connection()
    try:
        # Update task completion status
        conn.execute(
            'UPDATE schedule SET is_complete = ? WHERE id = ? AND user_id = ?',
            (1 if is_complete else 0, task_id, session['user_id'])
        )
        new_streak = 0
        
        # Streak Update Logic (only if task is completed)
        if is_complete:
            today_str = date.today().isoformat()
            yesterday_str = (date.today() - timedelta(days=1)).isoformat()
            user = conn.execute('SELECT last_activity_date, current_streak FROM users WHERE id = ?', (session['user_id'],)).fetchone()
            
            if user['last_activity_date'] == today_str:
                new_streak = user['current_streak']
            elif user['last_activity_date'] == yesterday_str:
                new_streak = user['current_streak'] + 1
                conn.execute(
                    'UPDATE users SET current_streak = ?, last_activity_date = ? WHERE id = ?',
                    (new_streak, today_str, session['user_id'])
                )
            else:
                new_streak = 1
                conn.execute(
                    'UPDATE users SET current_streak = 1, last_activity_date = ? WHERE id = ?',
                    (today_str, session['user_id'])
                )
            
            # --- *** ADDED BADGE LOGIC *** ---
            if new_streak >= 3:
                badge = conn.execute('SELECT id FROM badges WHERE name = ?', ('Streak Starter',)).fetchone()
                if badge:
                    exists = conn.execute(
                        'SELECT 1 FROM user_badges WHERE user_id = ? AND badge_id = ?',
                        (session['user_id'], badge['id'])
                    ).fetchone()
                    
                    if not exists:
                        conn.execute(
                            'INSERT INTO user_badges (user_id, badge_id) VALUES (?, ?)',
                            (session['user_id'], badge['id'])
                        )
                        flash("Badge Earned: Streak Starter! Achieved a 3-day study streak", 'success')
            # --- *** END OF BADGE LOGIC *** ---

        conn.commit()
        conn.close()
        return jsonify({"status": "success", "new_streak": new_streak})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500


# --- Community Routes ---

@app.route('/community')
@login_required
def community():
    exam_group = session.get('exam_group', 'Other')
    return render_template('community.html', exam_group=exam_group)

@app.route('/api/get_posts')
@login_required
def get_posts():
    channel = request.args.get('channel')
    exam_group = session.get('exam_group', 'Other') 
    
    if not channel:
        return jsonify({"error": "Channel not specified."}), 400

    conn = get_db_connection()
    post_rows = conn.execute(
        'SELECT p.id, p.content, p.media_url, p.created_at, p.user_id, u.username FROM posts p '
        'JOIN users u ON p.user_id = u.id '
        'WHERE p.exam_group = ? AND p.channel = ? AND p.parent_post_id IS NULL '
        'ORDER BY p.created_at DESC',
        (exam_group, channel)
    ).fetchall()
    conn.close()
    
    posts = []
    for row in post_rows:
        post = dict(row)
        post['created_at'] = str(datetime.strptime(post['created_at'], '%Y-%m-%d %H:%M:%S'))
        posts.append(post)
        
    return jsonify({"posts": posts})

@app.route('/api/get_replies')
@login_required
def get_replies():
    parent_id = request.args.get('post_id')
    if not parent_id:
        return jsonify({"error": "Post ID not specified."}), 400

    conn = get_db_connection()
    reply_rows = conn.execute(
        'SELECT p.id, p.content, p.media_url, p.created_at, p.user_id, u.username FROM posts p '
        'JOIN users u ON p.user_id = u.id '
        'WHERE p.parent_post_id = ? '
        'ORDER BY p.created_at ASC',
        (parent_id,)
    ).fetchall()
    conn.close()
    
    replies = []
    for row in reply_rows:
        reply = dict(row)
        reply['created_at'] = str(datetime.strptime(reply['created_at'], '%Y-%m-%d %H:%M:%S'))
        replies.append(reply)
        
    return jsonify({"replies": replies})

@app.route('/api/delete_post', methods=['POST'])
@login_required
def delete_post():
    data = request.get_json()
    post_id = data.get('post_id')
    user_id = session['user_id']
    
    if not post_id:
        return jsonify({"status": "error", "message": "Missing Post ID."}), 400

    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM posts WHERE parent_post_id = ?', (post_id,))
        result = conn.execute(
            'DELETE FROM posts WHERE id = ? AND user_id = ?',
            (post_id, user_id)
        )
        conn.commit()
        conn.close()
        
        if result.rowcount == 0:
            return jsonify({"status": "error", "message": "Post not found or permission denied."}), 403
            
        return jsonify({"status": "success", "message": "Post deleted."})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/add_post', methods=['POST'])
@login_required
def add_post():
    content = request.form.get('content')
    channel = request.form.get('channel')
    parent_post_id = request.form.get('parent_post_id')
    
    user_id = session['user_id']
    exam_group = session.get('exam_group', 'Other') 
    media_url = None

    if not content and 'file' not in request.files:
        return jsonify({"status": "error", "message": "Post must include text or a file."}), 400
    
    if not channel:
           return jsonify({"status": "error", "message": "Channel not specified."}), 400

    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '' and file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{user_id}_{int(datetime.now().timestamp())}_{filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            try:
                file.save(save_path)
                media_url = f"/static/uploads/{unique_filename}"
            except Exception as e:
                print(f"Error saving file: {e}")
                return jsonify({"status": "error", "message": "Failed to save uploaded file."}), 500
        elif file.filename != '':
            return jsonify({"status": "error", "message": "File type not allowed."}), 400
            
    try:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO posts (user_id, exam_group, channel, content, media_url, parent_post_id) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, exam_group, channel, content, media_url, parent_post_id)
        )
        conn.commit()
        conn.close()

        if not parent_post_id:
            conn_check = get_db_connection()
            post_count_row = conn_check.execute(
                'SELECT COUNT(*) FROM posts WHERE user_id = ? AND parent_post_id IS NULL',
                (user_id,)
            ).fetchone()
            post_count = post_count_row[0] if post_count_row else 0
            conn_check.close()
            
            if post_count == 1:
                award_badge(user_id, 'Community Poster')
        
        return jsonify({"status": "success", "message": "Post added."})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"status": "error", "message": str(e)}), 500


# --- Profile Routes ---

@app.route('/profile')
@login_required
def profile():
    conn = get_db_connection()
    user_row = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    badges_rows = conn.execute(
        """
        SELECT b.name, b.description, b.icon, ub.earned_at
        FROM user_badges ub
        JOIN badges b ON ub.badge_id = b.id
        WHERE ub.user_id = ?
        ORDER BY ub.earned_at DESC
        """,
        (session['user_id'],)
    ).fetchall()
    badges = [dict(row) for row in badges_rows]
    
    interview_rows = conn.execute(
        """
        SELECT id, score_confidence, score_clarity, feedback, strengths, completed_at
        FROM interviews
        WHERE user_id = ?
        ORDER BY completed_at DESC
        """,
        (session['user_id'],)
    ).fetchall()
    
    interviews = []
    for row in interview_rows:
        interview = dict(row)
        try:
            # Convert JSON strings back into Python lists
            interview['feedback'] = json.loads(row['feedback'])
            interview['strengths'] = json.loads(row['strengths'])
        except Exception as e:
            print(f"Error parsing interview JSON: {e}")
            interview['feedback'] = ["Error loading feedback."]
            interview['strengths'] = ["Error loading strengths."]
        
        # Format the date
        interview['completed_at_formatted'] = datetime.strptime(
            interview['completed_at'], '%Y-%m-%d %H:%M:%S'
        ).strftime('%B %d, %Y')
        
        interviews.append(interview)
    
    conn.close() 
    
    if user_row is None:
        return redirect(url_for('logout'))
        
    user = dict(user_row)
    user['created_at'] = datetime.strptime(user['created_at'], '%Y-%m-%d %H:%M:%S')
    stats = calculate_profile_stats(session['user_id'], 'all')
    
    return render_template(
        'profile.html', 
        user=user, 
        stats=stats, 
        badges=badges, 
        interviews=interviews
    )

@app.route('/api/get_profile_stats')
@login_required
def get_profile_stats():
    filter_period = request.args.get('filter', 'all')
    stats = calculate_profile_stats(session['user_id'], filter_period)
    return jsonify(stats)

@app.route('/change_stream', methods=['GET', 'POST'])
@login_required
def change_stream():
    conn = get_db_connection()
    if request.method == 'POST':
        new_group = request.form.get('stream')
        if not new_group:
            flash("Please choose a valid stream.", "warning")
            conn.close()
            return redirect(url_for('change_stream'))
        try:
            conn.execute('UPDATE users SET exam_group = ? WHERE id = ?', (new_group, session['user_id']))
            conn.commit()
            conn.close()
            session['exam_group'] = new_group
            flash("Stream updated successfully!", "success")
            return redirect(url_for('profile'))
        except Exception as e:
            conn.rollback()
            conn.close()
            flash(f"Could not update stream: {e}", "danger")
            return redirect(url_for('change_stream'))
    current_group = session.get('exam_group', 'Other')
    available_streams = list(PYQ_LINKS.keys())
    conn.close()
    return render_template('change_stream.html', current_group=current_group, available_streams=available_streams)

@app.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        user_id = session['user_id']
        try:
            conn = get_db_connection()
            conn.execute('DELETE FROM posts WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM schedule WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM user_progress WHERE user_id = ?', (user_id,))
            conn.execute('DELETE FROM interviews WHERE user_id = ?', (user_id,)) # Added interviews table
            conn.execute('DELETE FROM user_badges WHERE user_id = ?', (user_id,)) # Added user_badges table
            conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            try:
                conn.rollback()
                conn.close()
            except:
                pass
            flash(f"Failed to delete account: {e}", "danger")
            return redirect(url_for('profile'))
        session.clear()
        flash("Your account has been deleted.", "info")
        return redirect(url_for('index'))
    return render_template('delete_account_confirm.html')


@app.route('/flashcards')
@login_required 
def flashcards():
    """Renders the new AI Flashcard generator page."""
    return render_template('flashcards.html')


@app.route('/generate_flashcards', methods=['POST'])
@login_required 
def handle_generate_flashcards():
    """
    API endpoint to handle flashcard generation.
    Takes JSON, returns JSON.
    """
    data = request.get_json()
    topic = data.get('topic')
    num_cards_str = data.get('num_cards', 5) # Default to 5

    if not topic:
        return jsonify({"error": "A topic is required."}), 400

    try:
        num_cards = int(num_cards_str)
        if not 1 <= num_cards <= 20: # Set a reasonable limit
            return jsonify({"error": "Number of cards must be between 1 and 20."}), 400
    except ValueError:
        return jsonify({"error": "Invalid number of cards."}), 400
    except TypeError:
        return jsonify({"error": "Invalid number of cards."}), 400

    flashcard_data = ai_helper.generate_ai_flashcards(topic, num_cards)

    if isinstance(flashcard_data, dict) and "error" in flashcard_data:
        return jsonify(flashcard_data), 500

    return jsonify(flashcard_data)

@app.route('/revision_roulette')
@login_required
def revision_roulette():
    """
    Grabs all "weak" topics from the heatmap and generates a random
    7-day study plan.
    """
    
    all_topics_data = get_confidence_heatmap(session['user_id'])
    
    weak_topics = [
        item['ai_quiz_topic'] for item in all_topics_data 
        if item.get('confidence', 100) < 60
    ]
    
    revision_plan = []
    
    if not weak_topics:
        flash("We couldn't find any weak topics (< 60%) in your AI Quiz history. Great job!", "success")
    else:
        days_to_plan = min(len(weak_topics), 7)
        plan_topics = random.sample(weak_topics, days_to_plan)
        
        for i, topic in enumerate(plan_topics):
            revision_plan.append({
                "day": i + 1,
                "topic": topic
            })
            
    return render_template('revision_roulette.html', revision_plan=revision_plan)

@app.route('/interview_bot')
@login_required
def interview_bot():
    """
    Renders the interview bot page.
    Checks if the user's exam group is allowed.
    """
    allowed_groups = ['UPSC', 'Other']
    if session.get('exam_group') not in allowed_groups:
        flash("The Interview Bot is currently available for UPSC and Other streams.", "warning")
        return redirect(url_for('dashboard'))
        
    return render_template('interview_bot.html')

@app.route('/api/interview_chat', methods=['POST'])
@login_required
def api_interview_chat():
    """
    Handles a single turn in the interview chat.
    Receives the chat history and returns the AI's next response.
    """
    data = request.get_json()
    chat_history = data.get('history', [])
    user_stream = session.get('exam_group', 'Other') # Get user's stream

    if not chat_history:
        if user_stream == 'UPSC':
            chat_history = [{"role": "user", "content": "Start the interview."}]
        elif user_stream == 'Other':
            welcome_message = "Welcome. I see you're in the 'Other' stream. What specific interview are you preparing for today? (e.g., 'Google SWE', 'Medical School', 'Bank PO')"
            return jsonify({"answer": welcome_message})
            
    response = ai_helper.get_interview_response(chat_history)
    
    if isinstance(response, dict) and "error" in response:
        return jsonify({"error": response["error"]}), 500
        
    return jsonify({"answer": response})

@app.route('/api/interview_evaluate', methods=['POST'])
@login_required
def api_interview_evaluate():
    """
    Receives the final transcript, gets an evaluation,
    and saves everything to the database.
    """
    data = request.get_json()
    chat_history = data.get('history', [])
    
    if len(chat_history) < 3: # Need more than start, question, and answer
        return jsonify({"error": "Interview is too short to evaluate."}), 400

    # 1. Create a plain text transcript
    transcript_text = ""
    for message in chat_history:
        if message['role'] == 'user':
            transcript_text += f"Candidate: {message['content']}\n\n"
        elif message['role'] == 'assistant':
            transcript_text += f"Interviewer: {message['content']}\n\n"

    # 2. Get evaluation from AI
    evaluation_data = ai_helper.get_interview_evaluation(transcript_text)
    
    if isinstance(evaluation_data, dict) and "error" in evaluation_data:
        return jsonify({"error": evaluation_data["error"]}), 500

    # 3. Save to database
    try:
        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO interviews (user_id, transcript, score_confidence, score_clarity, feedback, strengths)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session['user_id'],
                transcript_text,
                evaluation_data.get('score_confidence'),
                evaluation_data.get('score_clarity'),
                json.dumps(evaluation_data.get('feedback', [])), # Store lists as JSON strings
                json.dumps(evaluation_data.get('strengths', [])) # Store lists as JSON strings
            )
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database save error: {e}")
        return jsonify({"error": "Failed to save interview results."}), 500

    # 4. Return the evaluation to the user
    return jsonify(evaluation_data)

# --- *** VISUALIZER ROUTE (SIMPLIFIED) *** ---
@app.route('/visualizer')
@login_required
def visualizer():
    """Renders the AI Concept Visualizer page."""
    return render_template('visualizer.html')

@app.route('/api/generate_diagram', methods=['POST'])
@login_required
def api_generate_diagram():
    """
    Takes a topic, asks the AI for Mermaid.js code,
    and returns that code to the frontend.
    """
    data = request.get_json()
    topic = data.get('topic')
    if not topic:
        return jsonify({"error": "A topic is required."}), 400

    # Call the diagram function (no more routing)
    diagram_data = ai_helper.generate_ai_diagram(topic)

    if isinstance(diagram_data, dict) and "error" in diagram_data:
        return jsonify(diagram_data), 500

    # Success! Return the JSON with the Mermaid code
    return jsonify(diagram_data) # This will be {"mermaid_code": "..."}

# --- *** AI STUDY ENVIRONMENT ROUTES *** ---
@app.route('/environment')
@login_required
def environment():
    """Renders the new AI Study Environment page."""
    return render_template('environment.html')


@app.route('/api/get_music', methods=['POST'])
@login_required
def api_get_music():
    """
    API endpoint to handle music recommendation generation.
    """
    data = request.get_json()
    mood = data.get('mood')
    genre = data.get('genre')

    if not mood or not genre:
        return jsonify({"error": "Mood and genre are required."}), 400

    # Note: This assumes you have generate_music_recommendation in ai_helper.py
    music_data = ai_helper.generate_music_recommendation(mood, genre)

    if isinstance(music_data, dict) and "error" in music_data:
        return jsonify(music_data), 500

    return jsonify(music_data)


if __name__ == '__main__':
    # Ensure the upload folder exists before running the app
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)