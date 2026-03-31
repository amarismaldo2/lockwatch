from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

app = Flask(__name__)
app.secret_key = "lockwatch_secret"

def init_db():
    conn = sqlite3.connect("lockwatch.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS login_logs (
        id INTEGER PRIMARY KEY,
        username TEXT,
        login_time TEXT,
        city TEXT,
        region TEXT,
        country TEXT
    )''')
    conn.commit()
    conn.close()

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect("lockwatch.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session["user"] = username
            log_login(username)
            anomaly = check_anomaly(username)
            session["anomaly"] = anomaly
            if anomaly:
                last_log = get_last_login(username)
                if last_log:
                    send_alert_email(username, last_log[0], last_log[1], last_log[2], last_log[3])
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

def log_login(username):
    try:
        res = requests.get("http://ip-api.com/json/")
        data = res.json()
        city = data.get("city", "Unknown")
        region = data.get("regionName", "Unknown")
        country = data.get("country", "Unknown")
    except:
        city = region = country = "Unknown"

    conn = sqlite3.connect("lockwatch.db")
    c = conn.cursor()
    c.execute("INSERT INTO login_logs (username, login_time, city, region, country) VALUES (?, ?, ?, ?, ?)",
              (username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), city, region, country))
    conn.commit()
    conn.close()

def get_last_login(username):
    conn = sqlite3.connect("lockwatch.db")
    c = conn.cursor()
    c.execute("SELECT login_time, city, region, country FROM login_logs WHERE username=? ORDER BY login_time DESC LIMIT 1", (username,))
    log = c.fetchone()
    conn.close()
    return log

def check_anomaly(username):
    conn = sqlite3.connect("lockwatch.db")
    c = conn.cursor()
    c.execute("SELECT login_time FROM login_logs WHERE username=?", (username,))
    logs = c.fetchall()
    conn.close()

    if len(logs) < 5:
        return False  # need more data to learn pattern

    hours = []
    for log in logs[:-1]:
        hour = datetime.strptime(log[0], "%Y-%m-%d %H:%M:%S").hour
        hours.append(hour)

    current_hour = datetime.now().hour
    avg_hour = sum(hours) / len(hours)

    # calculate standard deviation to learn YOUR normal range
    variance = sum((h - avg_hour) ** 2 for h in hours) / len(hours)
    std_dev = variance ** 0.5

    # flag if current hour is more than 2 standard deviations from your average
    deviation = abs(current_hour - avg_hour)
    if deviation > max(2 * std_dev, 2):  # at least 2hr buffer
        return True

    return False

def check_breach(password):
    import hashlib
    sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix = sha1[:5]
    suffix = sha1[5:]
    try:
        res = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}")
        hashes = res.text.splitlines()
        for line in hashes:
            h, count = line.split(":")
            if h == suffix:
                return int(count)  # returns how many times it was breached
        return 0
    except:
        return 0

def send_alert_email(username, login_time, city, region, country):
    sender = "amaris.maldo2@gmail.com"
    receiver = "amaris.maldo2@gmail.com"
    app_password = "ptgj izuu ohnb neyd"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "⚠️ LockWatch - Suspicious Login Detected"
    msg["From"] = sender
    msg["To"] = receiver

    html = f"""
    <div style="font-family: Poppins, sans-serif; background: #1a0025; padding: 40px; border-radius: 16px; max-width: 500px; margin: auto;">
        <h2 style="color: #e040fb;">⚠️ Suspicious Login Detected</h2>
        <p style="color: #e0b0ff;">A login was flagged on your LockWatch account.</p>
        <div style="background: rgba(255,100,100,0.1); border: 1px solid rgba(255,100,100,0.3); border-radius: 12px; padding: 16px; margin-top: 16px;">
            <p style="color: #ffaaaa;"><strong>User:</strong> {username}</p>
            <p style="color: #ffaaaa;"><strong>Time:</strong> {login_time}</p>
            <p style="color: #ffaaaa;"><strong>Location:</strong> {city}, {region}, {country}</p>
        </div>
        <p style="color: #9b6baa; margin-top: 16px; font-size: 0.85rem;">If this was you, no action needed. If not, change your password immediately.</p>
    </div>
    """

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, app_password)
        server.sendmail(sender, receiver, msg.as_string())

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    anomaly = session.get("anomaly", False)
    return render_template("dashboard.html", username=session["user"], anomaly=anomaly)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        from flask import jsonify
        breach_count = check_breach(password)
        if breach_count > 0:
            return jsonify({"error": f"This password was found in {breach_count:,} data breaches! Choose a different one."})
        try:
            conn = sqlite3.connect("lockwatch.db")
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return jsonify({"success": True})
        except sqlite3.IntegrityError:
            return jsonify({"error": "Username already taken"})
    return render_template("register.html")

@app.route("/history")
def history():
    if "user" not in session:
        return redirect(url_for("login"))
    conn = sqlite3.connect("lockwatch.db")
    c = conn.cursor()
    c.execute("SELECT login_time, city, region, country FROM login_logs WHERE username=? ORDER BY login_time DESC", (session["user"],))
    logs = c.fetchall()
    conn.close()
    return render_template("history.html", logs=logs, username=session["user"])

if __name__ == "__main__":
    init_db()
    app.run(debug=True)