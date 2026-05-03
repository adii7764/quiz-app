<div align="center">

# 🧠 QuizIQ

**A full-stack quiz platform — create, share & compete**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-quiz--app--tngt.onrender.com-7c6aff?style=for-the-badge&logo=render&logoColor=white)](https://quiz-app-tngt.onrender.com)
[![GitHub](https://img.shields.io/badge/GitHub-adii7764%2Fquiz--app-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/adii7764/quiz-app)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)

</div>

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 **Secure Auth** | Signup & login with Werkzeug password hashing |
| ✏️ **Create Quizzes** | Any user can build a quiz and share via a 6-character code |
| 🔑 **Join Quizzes** | Enter a code to attempt any quiz instantly |
| 📊 **Answer Review** | See correct/wrong/skipped breakdown after every submission |
| 🏆 **Leaderboard** | Live rankings with Chart.js bar, doughnut & histogram charts |
| 📜 **History** | Personal attempt history with score tracking |
| 👑 **Ownership** | Only the creator (or admin) can delete their quiz |
| 🌐 **Deployed** | Live on Render with Supabase PostgreSQL |

---

## 🛠 Tech Stack

**Backend**
- Python 3.14, Flask 3.1
- SQLite (local) / PostgreSQL via Supabase (production)
- Werkzeug — password hashing
- Gunicorn — production WSGI server

**Frontend**
- HTML5, CSS3, Vanilla JavaScript
- Chart.js 4.4 — leaderboard analytics
- Google Fonts — Syne + DM Sans
- Fully responsive dark UI

**DevOps**
- Render — web hosting (free tier)
- Supabase — managed PostgreSQL (free tier)
- python-dotenv — environment config

---

## 🚀 Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/adii7764/quiz-app.git
cd quiz-app

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Open .env and set your SECRET_KEY

# 4. Run
python app.py
```

Visit **http://localhost:5000**

> Default admin account: username `admin`, set your own password on signup

---

## 📁 Project Structure

```
quiz-app/
├── app.py                  # Flask routes, DB logic
├── requirements.txt
├── render.yaml             # Render deploy config
├── .env.example
├── static/
│   └── css/
│       └── style.css       # Full design system
└── templates/
    ├── login.html
    ├── signup.html
    ├── dashboard.html
    ├── join.html
    ├── quiz.html           # Timer + question navigation
    ├── result.html         # Score ring + answer review
    ├── leaderboard.html    # 4-tab chart analysis
    ├── history.html
    ├── admin.html          # Quiz builder
    ├── admin_quizzes.html
    ├── quiz_details.html
    └── error.html
```

---

## 📊 Leaderboard Charts

The leaderboard has 4 tabs of chart analysis:

- **Rankings** — player rows with mini progress bars
- **Performance** — best score vs average score (grouped bar)
- **Distribution** — score buckets as doughnut + histogram
- **By Quiz** — participation and avg score per quiz (dual-axis)

---

## 🔐 Security

- Passwords hashed with `werkzeug.security.generate_password_hash`
- `SECRET_KEY` loaded from environment variable (never hardcoded)
- Quiz delete protected by ownership check on both UI and backend
- `debug=False` in production

---

## 🌐 Deploy (Render + Supabase)

1. Create a free project on [supabase.com](https://supabase.com)
2. Copy the **Session Pooler** connection string
3. Push this repo to GitHub
4. Go to [render.com](https://render.com) → New → Web Service
5. Set environment variables:
   - `SECRET_KEY` → any random string
   - `DATABASE_URL` → your Supabase session pooler URI + `?sslmode=require`
6. Build command: `pip install -r requirements.txt`
7. Start command: `gunicorn app:app`

---

## 👨‍💻 Author

**Aditya Pandey**
B.Tech CSE, Galgotias University (2027)

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Aditya%20Pandey-0077B5?style=flat&logo=linkedin&logoColor=white)](https://linkedin.com/in/aditya-pandey-a6a958334)
[![GitHub](https://img.shields.io/badge/GitHub-adii7764-181717?style=flat&logo=github&logoColor=white)](https://github.com/adii7764)

---

<div align="center">
  <sub>Built with 💜 using Flask + Chart.js</sub>
</div>
