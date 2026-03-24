import os
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "securekey123"

# Fake database (we'll upgrade later)
users = {}

@app.route('/')
def home():
    return render_template("index.html")

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

    return '''
    <h2>Register</h2>
    <form method="POST">
        <input name="username" placeholder="Username"><br><br>
        <input name="password" placeholder="Password" type="password"><br><br>
        <button type="submit">Register</button>
    </form>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and users[username]["password"] == password:
            session['user'] = username
            return redirect('/dashboard')

    return '''
    <h2>Login</h2>
    <form method="POST">
        <input name="username" placeholder="Username"><br><br>
        <input name="password" placeholder="Password" type="password"><br><br>
        <button type="submit">Login</button>
    </form>
    '''

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    user = session['user']
    balance = users[user]["balance"]

    return f"""
    <h2>Welcome {user}</h2>
    <p>Balance: ₦{balance}</p>
    <a href="/logout">Logout</a>
    """

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
