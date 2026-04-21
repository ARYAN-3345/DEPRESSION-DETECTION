from flask import Flask, request, jsonify, session, render_template, url_for, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import sqlite3
import os
import smtplib
import random
import time
from modules.quiz import predict_result
from db import get_db, init_db

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.secret_key = "super_secret_key_123"

# ==============================
# PATH SETUP
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_PATH = os.path.join(BASE_DIR, "temp")

os.makedirs(os.path.join(BASE_DIR, "database"), exist_ok=True)
os.makedirs(TEMP_PATH, exist_ok=True)

# ==============================
# INIT DATABASE
# ==============================
init_db()

# ==============================
# OTP SYSTEM
# ==============================
otp_storage = {}
GMAIL = "depresensex@gmail.com"
APP_PASSWORD = "ntpf gyvg aiws icic"

def send_otp(email):
    otp = str(random.randint(100000, 999999))

    otp_storage[email] = {
        "otp": otp,
        "time": time.time()
    }

    subject = "Your OTP for DepreSenseX"
    body = f"Your OTP is: {otp} (valid for 5 minutes)"
    message = f"Subject: {subject}\n\n{body}"

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(GMAIL, APP_PASSWORD)
    server.sendmail(GMAIL, email, message)
    server.quit()

@app.route("/send_otp", methods=["POST"])
def send():
    email = request.form.get("email")

    if not email:
        return {"status": "error", "message": "Email required"}
    
    if email in otp_storage:
        if time.time() - otp_storage[email]["time"] < 30:
            return {"status": "error", "message": "Wait before requesting again"}

    try:
        send_otp(email)
        return {"status": "success"}
    except:
        return {"status": "error", "message": "Failed to send OTP"}

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    for key in list(otp_storage.keys()):
        if time.time() - otp_storage[key]["time"] > 300:
            otp_storage.pop(key)
        
    email = request.form.get("email")
    otp = request.form.get("otp")

    record = otp_storage.get(email)

    if not record:
        return {"status": "error", "message": "OTP not sent"}

    if time.time() - record["time"] > 300:
        otp_storage.pop(email)
        return {"status": "error", "message": "OTP expired"}

    if record["otp"] != otp:
        return {"status": "error", "message": "Invalid OTP"}

    session["otp_verified_email"] = email
    otp_storage.pop(email)

    return {"status": "success"}

# ==============================
# REGISTER
# ==============================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # validation
        if not name or not email or not password:
            flash("All fields required", "error")
            return redirect('/register')

        # OTP check
        if session.get("otp_verified_email") != email:
            flash("Please verify OTP first", "error")
            return redirect('/register')

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, hashed_password)
            )

            conn.commit()
            conn.close()

            # clear OTP session
            session.pop("otp_verified_email", None)

            flash("Account created successfully", "success")
            return redirect('/')

        except sqlite3.IntegrityError:
            flash("User already exists", "error")
            return redirect('/register')

    return render_template("register.html")

# ==============================
# HOME
# ==============================
@app.route('/')
def home():
    if 'user' in session:
        return redirect('/main')
    
    return render_template("index.html")

# ==============================
# LOGIN
# ==============================
@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        flash("Enter email and password", "error")
        return redirect('/')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cursor.fetchone()

    conn.close()

    if not user:
        flash("User does not exist", "error")
        return redirect('/')

    if not check_password_hash(user["password"], password):
        flash("Incorrect password", "error")
        return redirect('/')

    session['user'] = email
    session['user_name'] = user["name"]
    session.permanent = True

    return redirect('/main')

# ==============================
# MAIN DASHBOARD
# ==============================
@app.route('/main')
def main():
    if 'user' not in session:
        return redirect(url_for('home'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT prediction, score, type, date
        FROM results
        WHERE user_email=?
        ORDER BY date DESC
    """, (session['user'],))

    rows = cursor.fetchall()
    conn.close()

    has_data = len(rows) > 0

    return render_template(
        "main.html",
        has_data=has_data,
        results=rows,
        user_name=session.get("user_name")
    )

# ==============================
# ASSESSMENT PAGE
# ==============================
@app.route('/assessment')
def assessment():
    if 'user' not in session:
        return redirect(url_for('home'))

    return render_template('assessment.html', user_name=session.get("user_name"))

# ==============================
# TEXT QUIZ
# ==============================
@app.route('/text_quiz', methods=['GET'])
def text_quiz_page():
    if 'user' not in session:
        return redirect(url_for('home'))

    return render_template("text-quiz.html", user_name=session.get("user_name"))


@app.route('/text_quiz', methods=['POST'])
def text_quiz():

    if 'user' not in session:
        return jsonify({"status": "error"})

    data = request.get_json()
    answers = data.get("answers")

    if not answers or len(answers) != 9:
        return jsonify({"status": "error", "message": "Invalid answers"})
    
    if any(a is None for a in answers):
        return jsonify({"status": "error", "message": "Incomplete answers"})

    result = predict_result(answers)

    prediction = result["prediction"]

    raw_score = sum(answers)
    score = int((raw_score / 27) * 100)
    
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO results (user_email, prediction, score, type, details, confidence)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        session['user'],
        prediction,
        score,
        "quiz",
        str(answers),
        0
    ))

    conn.commit()
    conn.close()

    return jsonify({"status": "success"})

# ==============================
# VIDEO ANALYSIS
# ==============================
@app.route('/analyze_video', methods=['POST'])
def analyze_video():
    if 'user' not in session:
        return redirect(url_for('home'))

    file = request.files.get('video')

    if not file:
        return "No file"

    file_path = os.path.join(TEMP_PATH, f"{session['user']}_temp.webm")
    file.save(file_path)

    # Placeholder
    final_score = random.randint(30, 80)
    if final_score < 33:
        label = "Low"
    elif final_score < 66:
        label = "Medium"
    else:
        label = "High"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO results (user_email, prediction, score, type, details, confidence)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        session['user'],
        label,
        final_score,
        "video",
        "video analysis",
        0
    ))

    conn.commit()
    conn.close()

    return redirect(url_for('results_page'))

@app.route('/video_analysis')
def video_analysis():
    if 'user' not in session:
        return redirect(url_for('home'))

    return render_template('video-analysis.html', user_name=session.get("user_name"))

# ==============================
# FULL ASSESSMENT
# ==============================
@app.route('/full_assessment')
def full_assessment():
    if 'user' not in session:
        return redirect(url_for('home'))
    return "Coming soon"

# ==============================
# RESULTS PAGE
# ==============================
@app.route('/results_page')
def results_page():
    if 'user' not in session:
        return redirect(url_for('home'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT prediction, score, type, date
        FROM results
        WHERE user_email = ?
        ORDER BY date DESC
    """, (session['user'],))

    rows = cursor.fetchall()
    conn.close()

    results = [
        {
            "prediction": r["prediction"],
            "score": r["score"],
            "type": r["type"],
            "date": r["date"]
        }
        for r in rows
    ]

    latest = results[0] if results else None

    improvement = None
    if len(results) >= 2:
        improvement = results[0]['score'] - results[1]['score']

    return render_template(
        "results.html",
        results=results,
        latest=latest,
        improvement=improvement
    )
    
# ==============================
# HISTORY
# ==============================  
@app.route('/history')
def history():
    if 'user' not in session:
        return redirect(url_for('home'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, prediction, score, type, date
        FROM results
        WHERE user_email=?
        ORDER BY date DESC
    """, (session['user'],))

    results = cursor.fetchall()
    conn.close()

    return render_template("history.html", results=results)

# ==============================
# LOGOUT
# ==============================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# ==============================
# RUN
# ==============================
if __name__ == '__main__':
    app.run(debug=True)