from flask import Flask, render_template, request, redirect, session
import sqlite3
import random
import string

app = Flask(__name__)
app.secret_key = 'secret123'

# ------------------ DATABASE SETUP ------------------

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    password TEXT
                )''')
    # Scores table
    c.execute('''CREATE TABLE IF NOT EXISTS scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    score INTEGER,
                    total INTEGER,
                    code TEXT
                )''')

    # Questions table
    c.execute('''CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT,
                    option1 TEXT,
                    option2 TEXT,
                    option3 TEXT,
                    option4 TEXT,
                    answer TEXT
                )''')

    # Quiz rooms table
    c.execute('''CREATE TABLE IF NOT EXISTS quiz_rooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT,
                    question TEXT,
                    option1 TEXT,
                    option2 TEXT,
                    option3 TEXT,
                    option4 TEXT,
                    answer TEXT
                )''')

    # Scores table
    c.execute('''CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    code TEXT,
    score INTEGER,
    total INTEGER
                )''')

    conn.commit()
    conn.close()


def add_questions():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM questions")
    count = c.fetchone()[0]

    if count == 0:
        c.execute("INSERT INTO questions VALUES (NULL, ?, ?, ?, ?, ?, ?)",
                  ("Capital of India?", "Delhi", "Mumbai", "Chennai", "Kolkata", "Delhi"))

        c.execute("INSERT INTO questions VALUES (NULL, ?, ?, ?, ?, ?, ?)",
                  ("2 + 2 = ?", "3", "4", "5", "6", "4"))

    conn.commit()
    conn.close()


init_db()
add_questions()

# ------------------ ROUTES ------------------

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()

        conn.close()

        if user:
            session['user'] = username
            return redirect('/dashboard')
        else:
            return "Invalid Credentials ❌"

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))

        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('signup.html')


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    return render_template('dashboard.html', user=session['user'])


@app.route('/quiz')
def quiz():
    if 'user' not in session:
        return redirect('/')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT * FROM questions")
    questions = c.fetchall()

    conn.close()

    return render_template('quiz.html', questions=questions)

# ------------------ RESULT & LEADERBOARD ROUTES ------------------
@app.route('/result', methods=['POST'])
def result():
    if 'user' not in session:
        return redirect('/')

    username = session['user']
    code = session.get('quiz_code')  # must be set in /join

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # get questions for this quiz
    c.execute("SELECT * FROM quiz_rooms WHERE code=?", (code,))
    questions = c.fetchall()

    score = 0

    for q in questions:
        user_ans = request.form.get(f"q{q[0]}")
        if user_ans == q[7]:  # correct answer column
            score += 1

    total = len(questions)
    percentage = round((score / total) * 100) if total > 0 else 0

    # save score with code
    c.execute(
        "INSERT INTO scores (username, code, score, total) VALUES (?, ?, ?, ?)",
        (username, code, score, total)
    )

    conn.commit()
    conn.close()

    return render_template('result.html', score=score, total=total, percentage=percentage)


@app.route('/leaderboard')
def leaderboard():
    if 'user' not in session:
        return redirect('/')

    current_user = session['user']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("""
        SELECT username, MAX(score), total 
        FROM scores 
        GROUP BY username 
        ORDER BY MAX(score) DESC
    """)

    rows = c.fetchall()
    conn.close()

    data = []
    rank = 0
    prev_score = None
    count = 0

    for row in rows:
        count += 1
        score = row[1]

        if score != prev_score:
            rank = count

        data.append((rank, row[0], row[1], row[2], row[0] == current_user))
        prev_score = score

    return render_template('leaderboard.html', data=data)


@app.route('/delete_score', methods=['POST'])
def delete_score():
    if 'user' not in session:
        return redirect('/')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("DELETE FROM scores WHERE username=?", (session['user'],))

    conn.commit()
    conn.close()

    return redirect('/leaderboard')


@app.route('/history')
def history():
    if 'user' not in session:
        return redirect('/')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT score, total FROM scores WHERE username=? ORDER BY id DESC",
              (session['user'],))

    data = c.fetchall()
    conn.close()

    return render_template('history.html', data=data, user=session['user'])


@app.route('/admin')
def admin():
    if 'user' not in session or session['user'] != 'admin':
        return "Access Denied ❌"

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # get unique quiz codes
    c.execute("SELECT DISTINCT code FROM quiz_rooms")
    codes = c.fetchall()

    total = len(codes)

    conn.close()

    return render_template('admin.html', codes=codes, total=total)

# ------------------ QUIZ ROOM ROUTES ------------------
@app.route('/join', methods=['GET', 'POST'])
def join():
    if 'user' not in session:
        return redirect('/')

    if request.method == 'POST':
        code = request.form['code']
        username = session['user']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # CHECK QUIZ EXISTS
        c.execute("SELECT * FROM quiz_rooms WHERE code=?", (code,))
        questions = c.fetchall()

        if not questions:
            conn.close()
            return render_template('join.html', error="Invalid Code ❌")

        # CHECK ALREADY ATTEMPTED
        c.execute("SELECT * FROM scores WHERE username=? AND code=?", (username, code))
        already = c.fetchone()

        conn.close()

        if already:
            return render_template('join.html', error="Quiz Already Attempted ❌")

        # 🔥 VERY IMPORTANT LINE (ADD THIS)
        session['quiz_code'] = code

        return render_template('quiz.html', questions=questions, code=code)

    return render_template('join.html')

@app.route('/admin_generate', methods=['POST'])
def admin_generate():
    if 'user' not in session or session['user'] != 'admin':
        return "Access Denied ❌"

    data = request.get_json()
    questions = data['questions']

    if len(questions) < 2:
        return "Minimum 2 questions required ❌"

    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    for q in questions:
        c.execute("""
            INSERT INTO quiz_rooms (code, question, option1, option2, option3, option4, answer)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (code, q['question'], q['o1'], q['o2'], q['o3'], q['o4'], q['ans']))

    conn.commit()
    conn.close()

    return f"Quiz Code Generated: {code} 🎉"


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# VIEW ALL QUIZZES
@app.route('/admin/quizzes')
def view_quizzes():
    if 'user' not in session or session['user'] != 'admin':
        return "Access Denied ❌"

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT DISTINCT code FROM quiz_rooms")
    quizzes = c.fetchall()

    conn.close()

    return render_template('admin_quizzes.html', quizzes=quizzes)


# VIEW SINGLE QUIZ DETAILS
@app.route('/admin/quiz/<code>')
def quiz_details(code):
    if 'user' not in session or session['user'] != 'admin':
        return "Access Denied ❌"

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # get users who attempted this quiz
    c.execute("""
        SELECT username, score, total 
        FROM scores 
        WHERE code=? 
        ORDER BY score DESC
    """, (code,))

    rows = c.fetchall()
    conn.close()

    # ranking logic
    data = []
    rank = 0
    prev_score = None
    count = 0

    for row in rows:
        count += 1
        if row[1] != prev_score:
            rank = count

        data.append((rank, row[0], row[1], row[2]))
        prev_score = row[1]

    return render_template('quiz_details.html', data=data, code=code)

# DELETE QUIZ (ADMIN ONLY)
@app.route('/admin/delete_quiz/<code>', methods=['POST'])
def delete_quiz(code):
    if 'user' not in session or session['user'] != 'admin':
        return "Access Denied ❌"

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # delete quiz questions
    c.execute("DELETE FROM quiz_rooms WHERE code=?", (code,))

    # delete related scores
    c.execute("DELETE FROM scores WHERE code=?", (code,))

    conn.commit()
    conn.close()

    return redirect('/admin/quizzes')


if __name__ == '__main__':
    app.run(debug=True)