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
<!DOCTYPE html>
<html>
<head>
<title>Register</title>
<style>
body { background:#0f172a; color:white; font-family:Arial; text-align:center; padding-top:50px;}
input { padding:10px; margin:10px; width:200px; border-radius:5px; border:none;}
button { padding:10px 20px; background:#22c55e; border:none; color:white; border-radius:5px;}
a { color:#22c55e; display:block; margin-top:10px;}
</style>
</head>
<body>

<h2>Create Account</h2>

<form method="POST">
<input name="username" placeholder="Username"><br>
<input name="password" type="password" placeholder="Password"><br>
<button type="submit">Register</button>
</form>

<a href="/login">Already have an account? Login</a>

</body>
</html>
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
<!DOCTYPE html>
<html>
<head>
<title>Login</title>
<style>
body { background:#0f172a; color:white; font-family:Arial; text-align:center; padding-top:50px;}
input { padding:10px; margin:10px; width:200px; border-radius:5px; border:none;}
button { padding:10px 20px; background:#22c55e; border:none; color:white; border-radius:5px;}
a { color:#22c55e; display:block; margin-top:10px;}
</style>
</head>
<body>

<h2>Login</h2>

<form method="POST">
<input name="username" placeholder="Username"><br>
<input name="password" type="password" placeholder="Password"><br>
<button type="submit">Login</button>
</form>

<a href="/register">Don't have an account? Register</a>

</body>
</html>
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
