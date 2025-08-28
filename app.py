
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("QUIZ_SECRET_KEY", "dev_secret_change_me")
DB_PATH = os.path.join(os.path.dirname(__file__), "quiz.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    # Users
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    # Questions
    cur.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL CHECK (correct_option IN ('A','B','C','D'))
        )
    """)
    # Leaderboard / Scores
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            recorded_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()

    # Seed default questions if empty
    cur.execute("SELECT COUNT(*) as c FROM questions")
    count = cur.fetchone()["c"]
    if count == 0:
        sample_questions = [
            ("What is the capital of India?", "New Delhi", "Mumbai", "Kolkata", "Chennai", "A"),
            ("Which language runs in a web browser?", "C", "Java", "Python", "JavaScript", "D"),
            ("What does CPU stand for?", "Central Process Unit", "Central Processing Unit", "Control Processing Unit", "Computer Processing Unit", "B"),
            ("Which company developed the Python language?", "Microsoft", "Apple", "PSF", "None of the above", "C"),
            ("Which of the following is NOT a programming paradigm?", "OOP", "Functional", "Relational", "Procedural", "C"),
            ("Who is known as the father of computers?", "Charles Babbage", "Alan Turing", "Tim Berners-Lee", "John von Neumann", "A"),
            ("HTML stands for?", "HyperText Markup Language", "HighText Machine Language", "HyperText Markdown Language", "HyperTech Markup Language", "A"),
            ("Which protocol is used to send emails?", "HTTP", "SMTP", "FTP", "SSH", "B"),
            ("Which of these is a NoSQL database?", "MySQL", "PostgreSQL", "MongoDB", "SQLite", "C"),
            ("CSS is used for?", "Structuring content", "Styling web pages", "Programming logic", "Database queries", "B"),
        ]
        cur.executemany(
            "INSERT INTO questions (text, option_a, option_b, option_c, option_d, correct_option) VALUES (?, ?, ?, ?, ?, ?)",
            sample_questions
        )
        conn.commit()

    conn.close()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").strip()
        if not username or not password:
            flash("Username and password are required.", "error")
            return redirect(url_for("register"))
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                        (username, generate_password_hash(password), datetime.utcnow().isoformat()))
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Username already exists. Please choose another.", "error")
            conn.close()
            return redirect(url_for("register"))
        user_id = cur.lastrowid
        conn.close()
        session["user_id"] = user_id
        session["username"] = username
        # Reset any ongoing quiz state
        for k in ["quiz_order", "quiz_index", "quiz_score", "quiz_total"]:
            session.pop(k, None)
        return redirect(url_for("quiz"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").strip()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            # Reset any ongoing quiz state
            for k in ["quiz_order", "quiz_index", "quiz_score", "quiz_total"]:
                session.pop(k, None)
            return redirect(url_for("quiz"))
        else:
            flash("Invalid credentials.", "error")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("home"))

import random
from datetime import datetime

@app.route("/quiz", methods=["GET", "POST"])
@login_required
def quiz():
    conn = get_db()
    cur = conn.cursor()

    # Initialize quiz state if first time
    if "quiz_order" not in session:
        cur.execute("SELECT id FROM questions")
        ids = [row["id"] for row in cur.fetchall()]

        # 🔀 Shuffle for random order
        random.shuffle(ids)

        # (Optional) Limit to 5 random questions per quiz attempt
        # ids = random.sample(ids, min(5, len(ids)))

        session["quiz_order"] = ids
        session["quiz_index"] = 0
        session["quiz_score"] = 0
        session["quiz_total"] = len(ids)

    # Handle answer submission
    if request.method == "POST":
        selected = request.form.get("answer")
        qid = int(request.form.get("qid"))
        cur.execute("SELECT correct_option FROM questions WHERE id = ?", (qid,))
        correct = cur.fetchone()
        if correct and selected and selected.upper() == correct["correct_option"]:
            session["quiz_score"] = session.get("quiz_score", 0) + 1
        # Move to next question
        session["quiz_index"] = session.get("quiz_index", 0) + 1

    idx = session.get("quiz_index", 0)
    order = session.get("quiz_order", [])
    total = session.get("quiz_total", 0)

    # If finished, record score and go to results
    if idx >= total or total == 0:
        cur.execute("INSERT INTO scores (user_id, score, total, recorded_at) VALUES (?, ?, ?, ?)",
                    (session["user_id"], session.get("quiz_score", 0), total, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
        result_score = session.get("quiz_score", 0)
        # Clear quiz state
        for k in ["quiz_order", "quiz_index", "quiz_score", "quiz_total"]:
            session.pop(k, None)
        return redirect(url_for("result", score=result_score, total=total))

    # Fetch current question
    qid = order[idx]
    cur.execute("SELECT * FROM questions WHERE id = ?", (qid,))
    q = cur.fetchone()
    conn.close()

    return render_template("quiz.html", q=q, current=idx+1, total=total)

@app.route("/result")
@login_required
def result():
    score = int(request.args.get("score", 0))
    total = int(request.args.get("total", 0))
    return render_template("result.html", score=score, total=total)

@app.route("/leaderboard")
def leaderboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    # Top 10 scores (Leaderboard)
    cur.execute("""
        SELECT u.username, s.score, s.total, s.score * 1.0 / s.total AS pct, s.recorded_at
        FROM scores s
        JOIN users u ON s.user_id = u.id
        ORDER BY pct DESC, s.recorded_at ASC
        LIMIT 10
    """)
    top = [dict(username=row[0], score=row[1], total=row[2], pct=row[3], recorded_at=row[4]) for row in cur.fetchall()]

    # Current user’s attempts
    cur.execute("""
        SELECT score, total, score * 1.0 / total AS pct, recorded_at
        FROM scores
        WHERE user_id = ?
        ORDER BY recorded_at DESC
        LIMIT 10
    """, (session["user_id"],))
    attempts = [dict(score=row[0], total=row[1], pct=row[2], recorded_at=row[3]) for row in cur.fetchall()]

    conn.close()

    return render_template("leaderboard.html", top=top, attempts=attempts)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
