import json
import os
from flask import Flask, render_template, request, redirect, session, flash

app = Flask(__name__)
app.secret_key = "supersecretkey"

USERS_FILE = "users.json"
DEPOSITS_FILE = "deposits.json"
WITHDRAWALS_FILE = "withdrawals.json"

ADMIN_USERNAME = "Uwakmfon"


# -------- LOAD & SAVE --------
def load_data(file):
    if not os.path.exists(file):
        return [] if "deposits" in file or "withdrawals" in file else {}
    with open(file, "r") as f:
        return json.load(f)


def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f)


# -------- HOME --------
@app.route('/')
def home():
    return render_template('index.html')


# -------- REGISTER --------
@app.route('/register', methods=['GET', 'POST'])
def register():
    users = load_data(USERS_FILE)

    if request.method == 'POST':
        fullname = request.form.get('fullname')
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if not all([fullname, username, email, phone, password, confirm]):
            flash("All fields are required")
            return redirect('/register')

        if password != confirm:
            flash("Passwords do not match")
            return redirect('/register')

        if username in users:
            flash("Username already exists")
            return redirect('/register')

        users[username] = {
            "fullname": fullname,
            "email": email,
            "phone": phone,
            "password": password,
            "balance": 0
        }

        save_data(USERS_FILE, users)
        session['user'] = username

        flash("Registration successful")
        return redirect('/dashboard')

    return render_template('register.html')


# -------- LOGIN --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    users = load_data(USERS_FILE)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("All fields are required")
            return redirect('/login')

        if username not in users:
            flash("User does not exist")
            return redirect('/login')

        if users[username]['password'] != password:
            flash("Wrong password")
            return redirect('/login')

        session['user'] = username
        flash("Login successful")
        return redirect('/dashboard')

    return render_template('login.html')


# -------- DASHBOARD --------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    users = load_data(USERS_FILE)
    user = session['user']

    balance = users.get(user, {}).get('balance', 0)

    return render_template('dashboard.html', user=user, balance=balance)


# -------- DEPOSIT --------
@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        amount = request.form.get('amount')
        user = session['user']

        deposits = load_data(DEPOSITS_FILE)

        deposits.append({
            "user": user,
            "amount": amount,
            "status": "pending"
        })

        save_data(DEPOSITS_FILE, deposits)

        flash("Deposit submitted. Await confirmation")
        return redirect('/dashboard')

    return render_template('deposit.html')


# -------- MY DEPOSITS --------
@app.route('/my-deposits')
def my_deposits():
    if 'user' not in session:
        return redirect('/login')

    user = session['user']
    deposits = load_data(DEPOSITS_FILE)

    user_deposits = [d for d in deposits if d['user'] == user]

    return render_template('my_deposits.html', deposits=user_deposits)


# -------- WITHDRAW --------
@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user' not in session:
        return redirect('/login')

    users = load_data(USERS_FILE)
    user = session['user']
    error = None

    if request.method == 'POST':
        amount = request.form.get('amount')
        bank = request.form.get('bank')
        account = request.form.get('account')

        if not amount or not bank or not account:
            error = "All fields are required"

        else:
            amount = int(amount)

            if amount > users[user]['balance']:
                error = "Insufficient balance"
            else:
                withdrawals = load_data(WITHDRAWALS_FILE)

                withdrawals.append({
                    "user": user,
                    "amount": amount,
                    "bank": bank,
                    "account": account,
                    "status": "pending"
                })

                save_data(WITHDRAWALS_FILE, withdrawals)

                flash("Withdrawal request submitted")
                return redirect('/dashboard')

    return render_template('withdraw.html', error=error)


# -------- ADMIN DEPOSITS --------
@app.route('/admin/deposits')
def admin_deposits():
    if 'user' not in session or session['user'] != ADMIN_USERNAME:
        return redirect('/login')

    deposits = load_data(DEPOSITS_FILE)
    return render_template('admin_deposits.html', deposits=deposits)


# -------- APPROVE DEPOSIT --------
@app.route('/approve/<int:index>')
def approve(index):
    if 'user' not in session or session['user'] != ADMIN_USERNAME:
        return redirect('/login')

    deposits = load_data(DEPOSITS_FILE)
    users = load_data(USERS_FILE)

    if index < len(deposits):
        if deposits[index]['status'] == "pending":
            user = deposits[index]['user']
            amount = int(deposits[index]['amount'])

            if user in users:
                users[user]['balance'] += amount
                deposits[index]['status'] = "approved"

    save_data(DEPOSITS_FILE, deposits)
    save_data(USERS_FILE, users)

    flash("Deposit approved")
    return redirect('/admin/deposits')


# -------- REJECT DEPOSIT --------
@app.route('/reject/<int:index>')
def reject(index):
    if 'user' not in session or session['user'] != ADMIN_USERNAME:
        return redirect('/login')

    deposits = load_data(DEPOSITS_FILE)

    if index < len(deposits):
        if deposits[index]['status'] == "pending":
            deposits[index]['status'] = "rejected"

    save_data(DEPOSITS_FILE, deposits)

    flash("Deposit rejected")
    return redirect('/admin/deposits')


# -------- ADMIN WITHDRAWALS --------
@app.route('/admin/withdrawals')
def admin_withdrawals():
    if 'user' not in session or session['user'] != ADMIN_USERNAME:
        return redirect('/login')

    withdrawals = load_data(WITHDRAWALS_FILE)
    return render_template('admin_withdrawals.html', withdrawals=withdrawals)


# -------- APPROVE WITHDRAW --------
@app.route('/approve-withdraw/<int:index>')
def approve_withdraw(index):
    if 'user' not in session or session['user'] != ADMIN_USERNAME:
        return redirect('/login')

    withdrawals = load_data(WITHDRAWALS_FILE)
    users = load_data(USERS_FILE)

    if index < len(withdrawals):
        if withdrawals[index]['status'] == "pending":
            user = withdrawals[index]['user']
            amount = int(withdrawals[index]['amount'])

            if user in users and users[user]['balance'] >= amount:
                users[user]['balance'] -= amount
                withdrawals[index]['status'] = "approved"

    save_data(WITHDRAWALS_FILE, withdrawals)
    save_data(USERS_FILE, users)

    flash("Withdrawal approved")
    return redirect('/admin/withdrawals')


# -------- REJECT WITHDRAW --------
@app.route('/reject-withdraw/<int:index>')
def reject_withdraw(index):
    if 'user' not in session or session['user'] != ADMIN_USERNAME:
        return redirect('/login')

    withdrawals = load_data(WITHDRAWALS_FILE)

    if index < len(withdrawals):
        if withdrawals[index]['status'] == "pending":
            withdrawals[index]['status'] = "rejected"

    save_data(WITHDRAWALS_FILE, withdrawals)

    flash("Withdrawal rejected")
    return redirect('/admin/withdrawals')


# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully")
    return redirect('/')


# -------- RUN --------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
