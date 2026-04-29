from flask import Flask, render_template, request, redirect, session
import sqlite3

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

    conn.commit()
    conn.close()

def add_questions():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT,
                    option1 TEXT,
                    option2 TEXT,
                    option3 TEXT,
                    option4 TEXT,
                    answer TEXT
                )''')

    c.execute("SELECT COUNT(*) FROM questions")
    count = c.fetchone()[0]

    if count == 0:
        c.execute("INSERT INTO questions (question, option1, option2, option3, option4, answer) VALUES (?, ?, ?, ?, ?, ?)",
                  ("Capital of India?", "Delhi", "Mumbai", "Chennai", "Kolkata", "Delhi"))

        c.execute("INSERT INTO questions (question, option1, option2, option3, option4, answer) VALUES (?, ?, ?, ?, ?, ?)",
                  ("2 + 2 = ?", "3", "4", "5", "6", "4"))

    conn.commit()
    conn.close()

def create_scores_table():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    score INTEGER,
                    total INTEGER
                )''')

    conn.commit()
    conn.close()

init_db()
add_questions()
create_scores_table()

# ------------------ ROUTES ------------------

# LOGIN
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


# SIGNUP
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


# DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return render_template('dashboard.html', user=session['user'])
    return redirect('/')


# QUIZ
@app.route('/quiz', methods=['GET'])
def quiz():
    if 'user' not in session:
        return redirect('/')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT * FROM questions")
    questions = c.fetchall()

    conn.close()

    return render_template('quiz.html', questions=questions)


# RESULT + STORE SCORE
@app.route('/result', methods=['POST'])
def result():
    if 'user' not in session:
        return redirect('/')

    username = session['user']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT * FROM questions")
    questions = c.fetchall()

    score = 0

    for q in questions:
        user_ans = request.form.get(f"q{q[0]}")
        if user_ans == q[6]:
            score += 1

    total = len(questions)
    percentage = round((score / total) * 100) if total > 0 else 0

    # Store score
    c.execute("INSERT INTO scores (username, score, total) VALUES (?, ?, ?)",
              (username, score, total))

    conn.commit()
    conn.close()

    return render_template('result.html', score=score, total=total, percentage=percentage)


# LEADERBOARD
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

        # add current user info
        data.append((rank, row[0], row[1], row[2], row[0] == current_user))
        prev_score = score

    return render_template('leaderboard.html', data=data)

# LOGOUT
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')
# DELETE SCORE
@app.route('/delete_score', methods=['POST'])
def delete_score():
    if 'user' not in session:
        return redirect('/')

    username = session['user']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # delete ONLY this user's scores
    c.execute("DELETE FROM scores WHERE username=?", (username,))

    conn.commit()
    conn.close()

    return redirect('/leaderboard')
# HISTORY
@app.route('/history')
def history():
    if 'user' not in session:
        return redirect('/')

    username = session['user']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("""
        SELECT score, total 
        FROM scores 
        WHERE username=? 
        ORDER BY id DESC
    """, (username,))

    data = c.fetchall()

    conn.close()

    return render_template('history.html', data=data, user=username)


# RUN
if __name__ == '__main__':
    app.run(debug=True)