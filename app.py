from flask import Flask, render_template, request, redirect, session, jsonify
from contextlib import contextmanager
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import random
import string

app = Flask(__name__)
app.secret_key = 'secret123'

DB = 'database.db'

# ------------------ DATABASE ------------------

@contextmanager
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        c = conn.cursor()
        c.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            );
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                code TEXT,
                score INTEGER,
                total INTEGER
            );
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                option1 TEXT, option2 TEXT, option3 TEXT, option4 TEXT,
                answer TEXT
            );
            CREATE TABLE IF NOT EXISTS quiz_rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                question TEXT,
                option1 TEXT, option2 TEXT, option3 TEXT, option4 TEXT,
                answer TEXT,
                created_by TEXT DEFAULT 'admin'
            );
        ''')
        c.execute("SELECT COUNT(*) FROM questions")
        if c.fetchone()[0] == 0:
            c.executemany(
                "INSERT INTO questions VALUES (NULL,?,?,?,?,?,?)",
                [
                    ("Capital of India?", "Delhi", "Mumbai", "Chennai", "Kolkata", "Delhi"),
                    ("2 + 2 = ?", "3", "4", "5", "6", "4"),
                ]
            )
        conn.commit()


init_db()

# ------------------ DECORATORS ------------------

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect('/')
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session or session['user'] != 'admin':
            return render_template('error.html', message="Access Denied"), 403
        return f(*args, **kwargs)
    return decorated


# ------------------ ROUTES ------------------

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username=?", (username,)
            ).fetchone()
        if user and check_password_hash(user['password'], password):
            session['user'] = username
            return redirect('/dashboard')
        return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if not username or not password:
            return render_template('signup.html', error="All fields are required")
        with get_db() as conn:
            existing = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
            if existing:
                return render_template('signup.html', error="Username already taken")
            hashed = generate_password_hash(password)
            conn.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, hashed))
            conn.commit()
        return redirect('/')
    return render_template('signup.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=session['user'])


@app.route('/join', methods=['GET', 'POST'])
@login_required
def join():
    if request.method == 'POST':
        code = request.form['code'].strip().upper()
        username = session['user']
        with get_db() as conn:
            questions = conn.execute("SELECT * FROM quiz_rooms WHERE code=?", (code,)).fetchall()
            if not questions:
                return render_template('join.html', error="Invalid quiz code. Please try again.")
            already = conn.execute(
                "SELECT id FROM scores WHERE username=? AND code=?", (username, code)
            ).fetchone()
        if already:
            return render_template('join.html', error="You've already attempted this quiz.")
        session['quiz_code'] = code
        return render_template('quiz.html', questions=questions, code=code)
    return render_template('join.html')


@app.route('/result', methods=['POST'])
@login_required
def result():
    username = session['user']
    code = session.get('quiz_code')
    with get_db() as conn:
        questions = conn.execute("SELECT * FROM quiz_rooms WHERE code=?", (code,)).fetchall()
        review = []
        score = 0
        for q in questions:
            user_ans = request.form.get(f"q{q['id']}", None)
            correct = user_ans == q['answer']
            if correct:
                score += 1
            review.append({
                'question': q['question'],
                'options': [q['option1'], q['option2'], q['option3'], q['option4']],
                'correct': q['answer'],
                'user': user_ans,
                'is_correct': correct
            })
        total = len(questions)
        percentage = round((score / total) * 100) if total > 0 else 0
        conn.execute(
            "INSERT INTO scores (username, code, score, total) VALUES (?,?,?,?)",
            (username, code, score, total)
        )
        conn.commit()
    return render_template('result.html', score=score, total=total, percentage=percentage, review=review)


@app.route('/leaderboard')
@login_required
def leaderboard():
    current_user = session['user']
    with get_db() as conn:
        rows = conn.execute("""
            SELECT username, MAX(score) as best_score, total,
                   COUNT(*) as attempts,
                   ROUND(AVG(CAST(score AS REAL) / NULLIF(total,0) * 100), 1) as avg_pct,
                   MAX(CAST(score AS REAL) / NULLIF(total,0) * 100) as best_pct
            FROM scores
            GROUP BY username
            ORDER BY best_score DESC
        """).fetchall()

        # Per-quiz participation stats
        quiz_stats = conn.execute("""
            SELECT code, COUNT(DISTINCT username) as players,
                   ROUND(AVG(CAST(score AS REAL) / NULLIF(total,0) * 100), 1) as avg_pct
            FROM scores
            GROUP BY code
            ORDER BY players DESC
            LIMIT 8
        """).fetchall()

        # Score distribution buckets: 0-20, 20-40, 40-60, 60-80, 80-100
        dist = conn.execute("""
            SELECT
                SUM(CASE WHEN pct < 20  THEN 1 ELSE 0 END),
                SUM(CASE WHEN pct >= 20 AND pct < 40 THEN 1 ELSE 0 END),
                SUM(CASE WHEN pct >= 40 AND pct < 60 THEN 1 ELSE 0 END),
                SUM(CASE WHEN pct >= 60 AND pct < 80 THEN 1 ELSE 0 END),
                SUM(CASE WHEN pct >= 80 THEN 1 ELSE 0 END)
            FROM (
                SELECT CAST(score AS REAL) / NULLIF(total,0) * 100 as pct FROM scores
            )
        """).fetchone()

    data = []
    rank = None
    prev_score = None
    for i, row in enumerate(rows, 1):
        if row['best_score'] != prev_score:
            rank = i
        data.append({
            'rank': rank,
            'username': row['username'],
            'score': row['best_score'],
            'total': row['total'],
            'attempts': row['attempts'],
            'avg_pct': row['avg_pct'] or 0,
            'best_pct': round(row['best_pct'] or 0, 1),
            'is_me': row['username'] == current_user
        })
        prev_score = row['best_score']

    chart_data = {
        'bar_labels': [d['username'] for d in data[:10]],
        'bar_scores': [d['best_pct'] for d in data[:10]],
        'bar_avg': [d['avg_pct'] for d in data[:10]],
        'dist': list(dist) if dist else [0,0,0,0,0],
        'quiz_labels': [q['code'] for q in quiz_stats],
        'quiz_players': [q['players'] for q in quiz_stats],
        'quiz_avg': [q['avg_pct'] for q in quiz_stats],
    }

    return render_template('leaderboard.html', data=data, chart_data=chart_data)


@app.route('/delete_score', methods=['POST'])
@login_required
def delete_score():
    with get_db() as conn:
        conn.execute("DELETE FROM scores WHERE username=?", (session['user'],))
        conn.commit()
    return redirect('/leaderboard')


@app.route('/history')
@login_required
def history():
    with get_db() as conn:
        data = conn.execute(
            "SELECT score, total, code FROM scores WHERE username=? ORDER BY id DESC",
            (session['user'],)
        ).fetchall()
    return render_template('history.html', data=data, user=session['user'])


@app.route('/create')
@login_required
def create():
    user = session['user']
    with get_db() as conn:
        if user == 'admin':
            codes = conn.execute("SELECT DISTINCT code FROM quiz_rooms").fetchall()
        else:
            codes = conn.execute(
                "SELECT DISTINCT code FROM quiz_rooms WHERE created_by=?", (user,)
            ).fetchall()
    return render_template('admin.html', codes=codes, total=len(codes))


@app.route('/create_generate', methods=['POST'])
@login_required
def admin_generate():
    data = request.get_json()
    questions = data.get('questions', [])
    if len(questions) < 2:
        return jsonify(success=False, message="Minimum 2 questions required"), 400

    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    creator = session['user']
    with get_db() as conn:
        conn.executemany(
            "INSERT INTO quiz_rooms (code,question,option1,option2,option3,option4,answer,created_by) VALUES (?,?,?,?,?,?,?,?)",
            [(code, q['question'], q['o1'], q['o2'], q['o3'], q['o4'], q['ans'], creator) for q in questions]
        )
        conn.commit()
    return jsonify(success=True, code=code)


@app.route('/my-quizzes')
@login_required
def view_quizzes():
    user = session['user']
    with get_db() as conn:
        if user == 'admin':
            quizzes = conn.execute(
                "SELECT DISTINCT code, created_by FROM quiz_rooms ORDER BY id DESC"
            ).fetchall()
        else:
            quizzes = conn.execute(
                "SELECT DISTINCT code, created_by FROM quiz_rooms WHERE created_by=? ORDER BY id DESC",
                (user,)
            ).fetchall()
    return render_template('admin_quizzes.html', quizzes=quizzes)


@app.route('/quiz/<code>/results')
@login_required
def quiz_details(code):
    user = session['user']
    with get_db() as conn:
        # Only the creator or admin can view results
        owner = conn.execute(
            "SELECT created_by FROM quiz_rooms WHERE code=? LIMIT 1", (code,)
        ).fetchone()
        if not owner or (owner['created_by'] != user and user != 'admin'):
            return render_template('error.html', message="You don't have access to this quiz"), 403

        rows = conn.execute(
            "SELECT username, score, total FROM scores WHERE code=? ORDER BY score DESC",
            (code,)
        ).fetchall()

    data = []
    rank = prev_score = None
    for i, row in enumerate(rows, 1):
        if row['score'] != prev_score:
            rank = i
        data.append({'rank': rank, 'username': row['username'], 'score': row['score'], 'total': row['total']})
        prev_score = row['score']

    return render_template('quiz_details.html', data=data, code=code)


@app.route('/quiz/<code>/delete', methods=['POST'])
@login_required
def delete_quiz(code):
    user = session['user']
    with get_db() as conn:
        owner = conn.execute(
            "SELECT created_by FROM quiz_rooms WHERE code=? LIMIT 1", (code,)
        ).fetchone()
        if not owner or (owner['created_by'] != user and user != 'admin'):
            return render_template('error.html', message="You can't delete this quiz"), 403
        conn.execute("DELETE FROM quiz_rooms WHERE code=?", (code,))
        conn.execute("DELETE FROM scores WHERE code=?", (code,))
        conn.commit()
    return redirect('/my-quizzes')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
