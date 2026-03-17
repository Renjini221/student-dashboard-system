from flask import Flask, render_template, request, redirect, session, url_for
import os
import json

app = Flask(__name__)
app.secret_key = 'mysecretkey'
USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

@app.route('/')
def dashboard():
    if 'user' in session:
        users = load_users()
        email = session['user']
        if email in users:
            user_data = users[email]
            user_data['email'] = email
            return render_template('main.html', page='dashboard', data=user_data)
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        users = load_users()
        email = request.form['email']
        password = request.form['password']
        if email in users and users[email]['password'] == password:
            session['user'] = email
            return redirect('/')
        else:
            error = "Invalid credentials."
    return render_template('main.html', page='login', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        new_user = {
            "name": request.form['name'],
            "password": request.form['password'],
            "place": request.form['place'],
            "dob": request.form['dob'],
            "roll": request.form['roll'],
            "division": request.form['division']
        }
        email = request.form['email']

        users = load_users()
        if email in users:
            error = "User already exists."
        else:
            users[email] = new_user
            save_users(users)
            return redirect('/login')

    return render_template('main.html', page='register', error=error)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin':
            return redirect('/admin-select')
        else:
            error = "Invalid admin credentials."
    return render_template('main.html', page='admin-login', error=error)

@app.route('/admin-select', methods=['GET', 'POST'])
def admin_select():
    if request.method == 'POST':
        selected_div = request.form['division']
        return redirect(f'/admin-section?division={selected_div}')
    return render_template('main.html', page='admin-select')

@app.route('/admin-section', methods=['GET'])
def admin_section():
    division = request.args.get('division')
    filtered = []

    if division:
        users = load_users()
        for email, user in users.items():
            if user.get('division') == division:
                user['email'] = email
                filtered.append(user)

    return render_template('main.html', page='admin', users=filtered)

if __name__ == '__main__':
    app.run(debug=True)
