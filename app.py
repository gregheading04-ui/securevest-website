import json
import os
from flask import Flask, render_template, request, redirect, session

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
            return "All fields are required"

        if password != confirm:
            return "Passwords do not match"

        if username in users:
            return "Username already exists"

        users[username] = {
            "fullname": fullname,
            "email": email,
            "phone": phone,
            "password": password,
            "balance": 0,
            "message": ""
        }

        save_data(USERS_FILE, users)
        session['user'] = username

        users[username]['message'] = "Registration successful"
        save_data(USERS_FILE, users)

        return redirect('/dashboard')

    return render_template('register.html')


# -------- LOGIN --------

@app.route('/login', methods=['GET', 'POST'])
def login():
    users = load_users()
    error = None

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            error = "All fields are required"

        elif username not in users:
            error = "User does not exist"

        elif users[username]['password'] != password:
            error = "Wrong password"

        else:
            session['user'] = username
            return redirect('/dashboard')

    return render_template('login.html', error=error)

# -------- DASHBOARD --------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    users = load_data(USERS_FILE)
    user = session['user']

    balance = users.get(user, {}).get('balance', 0)

    message = users[user].get('message')

    # clear message after showing once
    users[user]['message'] = ""
    save_data(USERS_FILE, users)

    return render_template(
        'dashboard.html',
        user=user,
        balance=balance,
        message=message
    )


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

        users = load_data(USERS_FILE)
        users[user]['message'] = "Deposit submitted. Await confirmation"
        save_data(USERS_FILE, users)

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

    if request.method == 'POST':
        amount = request.form.get('amount')
        bank = request.form.get('bank')
        account = request.form.get('account')

        if not amount or not bank or not account:
            return "All fields are required"

        amount = int(amount)

        if amount > users[user]['balance']:
            return "Insufficient balance"

        withdrawals = load_data(WITHDRAWALS_FILE)

        withdrawals.append({
            "user": user,
            "amount": amount,
            "bank": bank,
            "account": account,
            "status": "pending"
        })

        save_data(WITHDRAWALS_FILE, withdrawals)

        users[user]['message'] = "Withdrawal request submitted"
        save_data(USERS_FILE, users)

        return redirect('/dashboard')

    return render_template('withdraw.html')


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

                users[user]['message'] = "Your deposit has been approved"

    save_data(DEPOSITS_FILE, deposits)
    save_data(USERS_FILE, users)

    return redirect('/admin/deposits')


# -------- REJECT DEPOSIT --------
@app.route('/reject/<int:index>')
def reject(index):
    if 'user' not in session or session['user'] != ADMIN_USERNAME:
        return redirect('/login')

    deposits = load_data(DEPOSITS_FILE)
    users = load_data(USERS_FILE)

    if index < len(deposits):
        if deposits[index]['status'] == "pending":
            user = deposits[index]['user']
            deposits[index]['status'] = "rejected"

            if user in users:
                users[user]['message'] = "Your deposit was rejected"

    save_data(DEPOSITS_FILE, deposits)
    save_data(USERS_FILE, users)

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

                users[user]['message'] = "Your withdrawal has been approved"

    save_data(WITHDRAWALS_FILE, withdrawals)
    save_data(USERS_FILE, users)

    return redirect('/admin/withdrawals')


# -------- REJECT WITHDRAW --------
@app.route('/reject-withdraw/<int:index>')
def reject_withdraw(index):
    if 'user' not in session or session['user'] != ADMIN_USERNAME:
        return redirect('/login')

    withdrawals = load_data(WITHDRAWALS_FILE)
    users = load_data(USERS_FILE)

    if index < len(withdrawals):
        if withdrawals[index]['status'] == "pending":
            user = withdrawals[index]['user']
            withdrawals[index]['status'] = "rejected"

            if user in users:
                users[user]['message'] = "Your withdrawal was rejected"

    save_data(WITHDRAWALS_FILE, withdrawals)
    save_data(USERS_FILE, users)

    return redirect('/admin/withdrawals')


# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')


# -------- RUN --------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
