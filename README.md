//🔐 LockWatch
A Python + Flask app that monitors logins for suspicious activity and sends real-time email alerts.

//Introduction
LockWatch is a security monitoring system that learns your normal login behavior and flags anything unusual.

Using your IP address and login timestamps, the system tracks where and when you log in. If something looks off — like a 3am login when you never log in at 3am — it sends you an email alert instantly.

Each suspicious login is flagged using:
1. **Anomaly detection** → login hour falls outside your normal range (standard deviation based)
2. **Location tracking** → every login logs your city, region, and country
3. **Breach detection** → passwords checked against HaveIBeenPwned at registration

Note: This project is designed to demonstrate real-world security concepts like behavioral analysis, k-anonymity, and alert systems!

## How It Works
1. User registers with a password checked against millions of known breached passwords
2. Every login is logged with a timestamp and IP-based location
3. Login hours are analyzed using standard deviation to build YOUR normal pattern
4. If a login falls outside your normal window, it is flagged as suspicious
5. An email alert is sent instantly with the login time and location

## Installation
1. Clone the repository
```
git clone https://github.com/amarismaldo2/lockwatch.git
```

2. Install dependencies
Python 3.13 required.
```
pip install flask requests
```

3. Set up your email alerts

In `app.py`, update the `send_alert_email` function with your Gmail and app password:
```
sender = "your_gmail@gmail.com"
app_password = "your_app_password"
```

4. Run the app
```
python app.py
```
Then go to `http://127.0.0.1:5000`

## Features
- 🔑 Secure registration and login
- 💪 Real-time password strength checker
- 🚨 HaveIBeenPwned breach detection
- 📍 IP-based location tracking on every login
- 🧠 Smart anomaly detection based on your personal login pattern
- 📜 Login history page with timestamps and locations
- 📧 Instant Gmail alerts on suspicious logins


```

Then run:
```
git add .
git commit -m "add README"
git push


Have funnn!! (yay) 😸🤍
MIT License © 2026 Amaris
