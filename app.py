from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Fake database (temporary)
users = {}

# -------- HOME --------
@app.route('/')
def home():
    return render_template('index.html')

# -------- LOGIN --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and users[username] == password:
            session['user'] = username
            return redirect('/dashboard')  # ✅ FIXED

        return "Invalid login details"

    return render_template('login.html')

# -------- REGISTER --------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        users[username] = password
        session['user'] = username
        return redirect('/dashboard')  # ✅ FIXED

    return render_template('register.html')

# -------- DASHBOARD --------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    return render_template('dashboard.html', user=session['user'])

# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# -------- RUN --------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
