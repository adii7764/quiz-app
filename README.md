# QuizIQ 🧠

A full-stack quiz platform where users can create, share, and attempt quizzes.

## Features
- 🔐 Secure auth with hashed passwords
- ✏️ Every user can create quizzes and share via code
- 🔑 Join any quiz with a 6-character code
- 📊 Answer review after submission (correct/wrong/skipped)
- 🏆 Leaderboard with chart analysis
- 📜 Personal quiz history
- 👑 Creators can only delete their own quizzes

## Local Setup
```bash
git clone <your-repo>
cd quiz-app-improved
pip install -r requirements.txt
cp .env.example .env        # edit SECRET_KEY
python app.py
```
Visit `http://localhost:5000`

## Deploy on Render

1. Push code to GitHub
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect your repo — Render reads `render.yaml` automatically
4. It will create a **web service** + **free PostgreSQL** database
5. Set `SECRET_KEY` in Environment Variables on Render dashboard
6. Deploy 🚀

## Tech Stack
- **Backend** — Flask, Python
- **Database** — SQLite (local) / PostgreSQL (production)
- **Frontend** — HTML, CSS, Vanilla JS, Chart.js
- **Auth** — Werkzeug password hashing
- **Deploy** — Gunicorn + Render
