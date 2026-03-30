import sqlite3
import os
from flask import Flask, render_template, request, redirect, session, flash

app = Flask(__name__)
app.secret_key = "supersecretkey"

ADMIN_USERNAME = "Uwakmfon"
DB_FILE = "database.db"

# -------- DB CONNECT --------
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# -------- CREATE TABLES --------
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        balance INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS deposits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        amount INTEGER,
        status TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        amount INTEGER,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -------- HOME --------
@app.route('/')
def home():
    return render_template('index.html')

# -------- REGISTER --------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db()
        cur = conn.cursor()

        # check user
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        if cur.fetchone():
            return "User already exists"

        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()

        session['user'] = username
        flash("Registration successful")
        return redirect('/dashboard')

    return render_template('register.html')

# -------- LOGIN --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()

        if not username or not password:
            error = "All fields required"

        elif not user:
            error = "User does not exist"

        elif user["password"] != password:
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

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT balance FROM users WHERE username=?", (session['user'],))
    user = cur.fetchone()

    balance = user["balance"] if user else 0

    message = None
    messages = session.pop('_flashes', [])
    if messages:
        message = messages[0][1]

    return render_template('dashboard.html', user=session['user'], balance=balance, message=message)

# -------- DEPOSIT --------
@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        amount = int(request.form.get('amount'))

        # ✅ Minimum check
        if amount < 2000:
            flash("Minimum deposit is ₦2000")
            return redirect('/dashboard')

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO deposits (user, amount, status) VALUES (?, ?, ?)",
            (session['user'], amount, "pending")
        )

        conn.commit()
        conn.close()

        flash("Deposit submitted")
        return redirect('/dashboard')

    return render_template('deposit.html')

# -------- MY DEPOSITS --------
@app.route('/my-deposits')
def my_deposits():
    if 'user' not in session:
        return redirect('/login')

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM deposits WHERE user=?", (session['user'],))
    deposits = cur.fetchall()

    return render_template('my_deposits.html', deposits=deposits)

# -------- ADMIN DEPOSITS --------
@app.route('/admin/deposits')
def admin_deposits():
    if session.get('user') != ADMIN_USERNAME:
        return redirect('/dashboard')

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM deposits")
    deposits = cur.fetchall()

    return render_template('admin_deposits.html', deposits=deposits)

# -------- APPROVE DEPOSIT --------
@app.route('/approve-deposit/<int:id>')
def approve_deposit(id):
    if session.get('user') != ADMIN_USERNAME:
        return redirect('/dashboard')

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM deposits WHERE id=?", (id,))
    d = cur.fetchone()

    if d:
        cur.execute("UPDATE deposits SET status='approved' WHERE id=?", (id,))
        cur.execute("UPDATE users SET balance = balance + ? WHERE username=?", (d["amount"], d["user"]))

    conn.commit()
    conn.close()

    return redirect('/admin/deposits')

# -------- REJECT DEPOSIT --------
@app.route('/reject-deposit/<int:id>')
def reject_deposit(id):
    if session.get('user') != ADMIN_USERNAME:
        return redirect('/dashboard')

    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE deposits SET status='rejected' WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect('/admin/deposits')

# -------- WITHDRAW --------
@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        amount = int(request.form.get('amount'))

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT balance FROM users WHERE username=?", (session['user'],))
        user = cur.fetchone()

        if user["balance"] < amount:
            flash("Insufficient balance")
            return redirect('/dashboard')

        cur.execute("INSERT INTO withdrawals (user, amount, status) VALUES (?, ?, ?)",
                    (session['user'], amount, "pending"))

        conn.commit()
        conn.close()

        flash("Withdrawal submitted")
        return redirect('/dashboard')

    return render_template('withdraw.html')

# -------- ADMIN WITHDRAW --------
@app.route('/admin/withdrawals')
def admin_withdrawals():
    if session.get('user') != ADMIN_USERNAME:
        return redirect('/dashboard')

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM withdrawals")
    withdrawals = cur.fetchall()

    return render_template('admin_withdrawals.html', withdrawals=withdrawals)

# -------- APPROVE WITHDRAW --------
@app.route('/approve-withdraw/<int:id>')
def approve_withdraw(id):
    if session.get('user') != ADMIN_USERNAME:
        return redirect('/dashboard')

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM withdrawals WHERE id=?", (id,))
    w = cur.fetchone()

    if w:
        cur.execute("UPDATE withdrawals SET status='approved' WHERE id=?", (id,))
        cur.execute("UPDATE users SET balance = balance - ? WHERE username=?", (w["amount"], w["user"]))

    conn.commit()
    conn.close()

    return redirect('/admin/withdrawals')

# -------- REJECT WITHDRAW --------
@app.route('/reject-withdraw/<int:id>')
def reject_withdraw(id):
    if session.get('user') != ADMIN_USERNAME:
        return redirect('/dashboard')

    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE withdrawals SET status='rejected' WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect('/admin/withdrawals')

# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out")
    return redirect('/login')

# -------- RUN --------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
