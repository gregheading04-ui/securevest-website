import json
import os
from flask import Flask, render_template, request, redirect, session, flash

app = Flask(__name__)
app.secret_key = "supersecretkey"

USERS_FILE = "users.json"
DEPOSITS_FILE = "deposits.json"
WITHDRAWALS_FILE = "withdrawals.json"

ADMIN_USERNAME = "Uwakmfon"

# -------- SAFE LOAD --------
def load_json(file):
    if not os.path.exists(file):
        return {} if "users" in file else []
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return {} if "users" in file else []

# -------- SAVE --------
def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

# -------- HOME --------
@app.route('/')
def home():
    return render_template('index.html')

# -------- REGISTER --------
@app.route('/register', methods=['GET', 'POST'])
def register():
    users = load_json(USERS_FILE)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return "All fields required"

        if username in users:
            return "User already exists"

        users[username] = {
            "password": password,
            "balance": 0
        }

        save_json(USERS_FILE, users)
        session['user'] = username
        flash("Registration successful")

        return redirect('/dashboard')

    return render_template('register.html')

# -------- LOGIN --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    users = load_json(USERS_FILE)
    error = None

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if username == "" or password == "":
            error = "All fields are required"

        elif username not in users:
            error = "User does not exist"

        elif users[username].get('password') != password:
            error = "Wrong password"

        else:
            session['user'] = username
            flash("Login successful")
            return redirect('/dashboard')

    return render_template('login.html', error=error)

# -------- DASHBOARD --------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    users = load_json(USERS_FILE)
    user = session['user']
    balance = users.get(user, {}).get("balance", 0)

    message = None
    messages = session.pop('_flashes', [])

    if messages:
        message = messages[0][1]

    return render_template('dashboard.html', user=user, balance=balance, message=message)

# -------- DEPOSIT --------
@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        amount = request.form.get('amount')
        deposits = load_json(DEPOSITS_FILE)

        deposits.append({
            "user": session['user'],
            "amount": amount,
            "status": "pending"
        })

        save_json(DEPOSITS_FILE, deposits)

        flash("Deposit submitted. Await confirmation")
        return redirect('/dashboard')

    return render_template('deposit.html')

# -------- MY DEPOSITS --------
@app.route('/my-deposits')
def my_deposits():
    if 'user' not in session:
        return redirect('/login')

    deposits = load_json(DEPOSITS_FILE)
    user_deposits = [d for d in deposits if d['user'] == session['user']]

    return render_template('my_deposits.html', deposits=user_deposits)

# -------- ADMIN DEPOSITS --------
@app.route('/admin/deposits')
def admin_deposits():
    if session.get('user') != ADMIN_USERNAME:
        return redirect('/dashboard')

    deposits = load_json(DEPOSITS_FILE)
    return render_template('admin_deposits.html', deposits=deposits)

# -------- APPROVE DEPOSIT --------
@app.route('/approve-deposit/<int:index>')
def approve_deposit(index):
    if session.get('user') != ADMIN_USERNAME:
        return redirect('/dashboard')

    deposits = load_json(DEPOSITS_FILE)
    users = load_json(USERS_FILE)

    if 0 <= index < len(deposits):
        d = deposits[index]
        d['status'] = "approved"

        user = d['user']
        amount = int(d['amount'])

        users[user]['balance'] += amount

    save_json(DEPOSITS_FILE, deposits)
    save_json(USERS_FILE, users)

    return redirect('/admin/deposits')

# -------- REJECT DEPOSIT --------
@app.route('/reject-deposit/<int:index>')
def reject_deposit(index):
    if session.get('user') != ADMIN_USERNAME:
        return redirect('/dashboard')

    deposits = load_json(DEPOSITS_FILE)

    if 0 <= index < len(deposits):
        deposits[index]['status'] = "rejected"

    save_json(DEPOSITS_FILE, deposits)

    return redirect('/admin/deposits')

# -------- WITHDRAW --------
@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        amount = int(request.form.get('amount'))
        users = load_json(USERS_FILE)

        if users[session['user']]['balance'] < amount:
            flash("Insufficient balance")
            return redirect('/dashboard')

        withdrawals = load_json(WITHDRAWALS_FILE)

        withdrawals.append({
            "user": session['user'],
            "amount": amount,
            "status": "pending"
        })

        save_json(WITHDRAWALS_FILE, withdrawals)

        flash("Withdrawal request submitted")
        return redirect('/dashboard')

    return render_template('withdraw.html')

# -------- ADMIN WITHDRAWALS --------
@app.route('/admin/withdrawals')
def admin_withdrawals():
    if session.get('user') != ADMIN_USERNAME:
        return redirect('/dashboard')

    withdrawals = load_json(WITHDRAWALS_FILE)
    return render_template('admin_withdrawals.html', withdrawals=withdrawals)

# -------- APPROVE WITHDRAW --------
@app.route('/approve-withdraw/<int:index>')
def approve_withdraw(index):
    if session.get('user') != ADMIN_USERNAME:
        return redirect('/dashboard')

    withdrawals = load_json(WITHDRAWALS_FILE)
    users = load_json(USERS_FILE)

    if 0 <= index < len(withdrawals):
        w = withdrawals[index]
        w['status'] = "approved"

        user = w['user']
        amount = int(w['amount'])

        users[user]['balance'] -= amount

    save_json(WITHDRAWALS_FILE, withdrawals)
    save_json(USERS_FILE, users)

    return redirect('/admin/withdrawals')

# -------- REJECT WITHDRAW --------
@app.route('/reject-withdraw/<int:index>')
def reject_withdraw(index):
    if session.get('user') != ADMIN_USERNAME:
        return redirect('/dashboard')

    withdrawals = load_json(WITHDRAWALS_FILE)

    if 0 <= index < len(withdrawals):
        withdrawals[index]['status'] = "rejected"

    save_json(WITHDRAWALS_FILE, withdrawals)

    return redirect('/admin/withdrawals')

# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully")
    return redirect('/login')

# -------- RUN --------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
