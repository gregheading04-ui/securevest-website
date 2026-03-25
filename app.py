import json
import os
from flask import Flask, render_template, request, redirect, session, flash

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
    error = None

    if request.method == 'POST':
        fullname = request.form['fullname']
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validation
        if not fullname or not username or not email or not phone or not password:
            error = "All fields are required"

        elif password != confirm_password:
            error = "Passwords do not match"

        elif username in users:
            error = "Username already exists"

        else:
            users[username] = {
                "fullname": fullname,
                "email": email,
                "phone": phone,
                "password": password,
                "balance": 0
            }

            save_users(users)
            session['user'] = username
            return redirect('/dashboard')

    return render_template('register.html', error=error)
# -------- LOGIN --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    users = load_users()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

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

    users = load_users()
    user = session['user']

    balance = users.get(user, {}).get('balance', 0)

    # Load deposits
    if not os.path.exists("deposits.json"):
        deposits = []
    else:
        with open("deposits.json", "r") as f:
            deposits = json.load(f)

    # Get this user's deposits
    user_deposits = [d for d in deposits if d['user'] == user]

    message = None

    if user_deposits:
        last = user_deposits[-1]

        if last['status'] == "approved":
            message = f"✅ Your deposit of ₦{last['amount']} was approved"

        elif last['status'] == "rejected":
            message = f"❌ Your deposit of ₦{last['amount']} was rejected"

        else:
            message = f"⏳ Your deposit of ₦{last['amount']} is pending"

    return render_template('dashboard.html', user=user, balance=balance, message=message)
# -------- DEPOSIT --------
@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        amount = request.form.get('amount')
        user = session['user']

        if not os.path.exists("deposits.json"):
            deposits = []
        else:
            with open("deposits.json", "r") as f:
                deposits = json.load(f)

        deposits.append({
            "user": user,
            "amount": amount,
            "status": "pending"
        })

        with open("deposits.json", "w") as f:
            json.dump(deposits, f)

        flash("Deposit submitted successfully! Await confirmation.")
        return redirect('/dashboard')

    return render_template("deposit.html")
    
@app.route('/admin/deposits')
def admin_deposits():
    if 'user' not in session or session['user'] != 'Uwakmfon':
        return redirect('/login')

    if not os.path.exists("deposits.json"):
        deposits = []
    else:
        with open("deposits.json", "r") as f:
            deposits = json.load(f)

    return render_template('admin_deposits.html', deposits=deposits)

@app.route('/approve/<int:index>')
def approve_deposit(index):
    if 'user' not in session or session['user'] != 'Uwakmfon':
        return redirect('/login')

    if not os.path.exists("deposits.json"):
        return redirect('/admin/deposits')

    with open("deposits.json", "r") as f:
        deposits = json.load(f)

    if index < len(deposits):
        # 🚨 Only process if still pending
        if deposits[index]['status'] == "pending":
            deposits[index]['status'] = "approved"

            users = load_users()
            user = deposits[index]['user']
            amount = int(deposits[index]['amount'])

            if user in users:
                users[user]['balance'] += amount
                save_users(users)

    with open("deposits.json", "w") as f:
        json.dump(deposits, f)

    return redirect('/admin/deposits')

@app.route('/reject/<int:index>')
def reject_deposit(index):
    if 'user' not in session or session['user'] != 'Uwakmfon':
        return redirect('/login')

    if not os.path.exists("deposits.json"):
        return redirect('/admin/deposits')

    with open("deposits.json", "r") as f:
        deposits = json.load(f)

    if index < len(deposits):
        # 🚨 Only reject if still pending
        if deposits[index]['status'] == "pending":
            deposits[index]['status'] = "rejected"

    with open("deposits.json", "w") as f:
        json.dump(deposits, f)

    return redirect('/admin/deposits')
    
# -------- MY DEPOSITS --------
@app.route('/my-deposits')
def my_deposits():
    if 'user' not in session:
        return redirect('/login')

    user = session['user']

    if not os.path.exists("deposits.json"):
        deposits = []
    else:
        with open("deposits.json", "r") as f:
            deposits = json.load(f)

    user_deposits = [d for d in deposits if d['user'] == user]

    return render_template('my_deposits.html', deposits=user_deposits)

# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# -------- RUN --------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
