from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'secret123'  # Required for session

# Create database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    password TEXT
                )''')
    conn.commit()
    conn.close()

init_db()
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

    # Insert sample questions (only once)
    c.execute("SELECT COUNT(*) FROM questions")
    count = c.fetchone()[0]

    if count == 0:
        c.execute("INSERT INTO questions (question, option1, option2, option3, option4, answer) VALUES (?, ?, ?, ?, ?, ?)",
                  ("Capital of India?", "Delhi", "Mumbai", "Chennai", "Kolkata", "Delhi"))

        c.execute("INSERT INTO questions (question, option1, option2, option3, option4, answer) VALUES (?, ?, ?, ?, ?, ?)",
                  ("2 + 2 = ?", "3", "4", "5", "6", "4"))

    conn.commit()
    conn.close()

add_questions()

# LOGIN ROUTE
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
            session['user'] = username   # store user in session
            return redirect('/dashboard')
        else:
            return "Invalid Credentials ❌"

    return render_template('login.html')


# SIGNUP ROUTE
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


# DASHBOARD ROUTE
@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return render_template('dashboard.html', user=session['user'])
    else:
        return redirect('/')


# LOGOUT ROUTE
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'user' not in session:
        return redirect('/')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT * FROM questions")
    questions = c.fetchall()

    conn.close()

    return render_template('quiz.html', questions=questions)
@app.route('/result', methods=['POST'])
def result():
    if 'user' not in session:
        return redirect('/')

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

    conn.close()

    return render_template('result.html', score=score, total=total, percentage=percentage)


if __name__ == '__main__':
    app.run(debug=True)