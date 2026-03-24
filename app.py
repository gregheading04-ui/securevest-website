import os
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "securekey123"

# Temporary database
users = {}

@app.route('/')
def home():
    return render_template("index.html")

# -------- REGISTER --------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        users[username] = {
            "password": password,
            "balance": 0
        }

        return redirect('/login')

    return render_template("register.html")

# -------- LOGIN --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and users[username]["password"] == password:
            session['user'] = username
            return redirect('/dashboard')

    return render_template("login.html")

# -------- DASHBOARD --------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    user = session['user']
    balance = users[user]["balance"]

    return render_template("dashboard.html", user=user, balance=balance)

# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
