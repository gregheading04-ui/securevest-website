import json
import os
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATA_FILE = "users.json"

# -------- LOAD USERS --------
def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# -------- SAVE USERS --------
def save_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f)

# -------- HOME --------
@app.route('/')
def home():
    return render_template('index.html')

# -------- REGISTER --------
@app.route('/register', methods=['GET', 'POST'])
def register():
    users = load_users()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users:
            return "User already exists"

        users[username] = {
            "password": password,
            "balance": 0
        }

        save_users(users)
        session['user'] = username
        return redirect('/dashboard')

    return render_template('register.html')

# -------- LOGIN --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    users = load_users()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and users[username]["password"] == password:
            session['user'] = username
            return redirect('/dashboard')

        return "Invalid login details"

    return render_template('login.html')

# -------- DASHBOARD --------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    users = load_users()
    user = session['user']
    balance = users[user]["balance"]

    return render_template('dashboard.html', user=user, balance=balance)
# -------- DEPOSIT --------
@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        amount = request.form['amount']
        user = session['user']

        # Load deposits
        if not os.path.exists("deposits.json"):
            deposits = []
        else:
            with open("deposits.json", "r") as f:
                deposits = json.load(f)

        # Add new deposit
        deposits.append({
            "user": user,
            "amount": amount,
            "status": "pending"
        })

        # Save deposits
        with open("deposits.json", "w") as f:
            json.dump(deposits, f)

        return redirect('/dashboard')

    return render_template("deposit.html")
# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# -------- RUN --------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
