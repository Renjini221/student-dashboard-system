from flask import Flask, render_template, request, redirect, session
import os
import json

app = Flask(__name__)
app.secret_key = 'mysecretkey'
USERS_FILE = 'users.json'


def load_users():
    """Load saved users from disk."""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {}
    return {}


def save_users(users):
    """Persist users to disk."""
    with open(USERS_FILE, 'w') as file:
        json.dump(users, file, indent=4)


@app.route('/')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    users = load_users()
    email = session['user']
    user_data = users.get(email)

    if not user_data:
        session.pop('user', None)
        return redirect('/login')

    user_info = dict(user_data)
    user_info['email'] = email
    if 'cls' not in user_info:
        user_info['cls'] = user_info.get('class_name')
    if 'div' not in user_info:
        user_info['div'] = user_info.get('division')
    _ensure_marks(user_info)
    return render_template('main.html', page='dashboard', data=user_info)


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
            "div": request.form['division'],
            "cls": request.form['cls'],
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
    session.pop('admin', None)
    return redirect('/login')


@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin':
            session['admin'] = True
            return redirect('/admin-select')
        error = "Invalid admin credentials."

    return render_template('main.html', page='admin-login', error=error)


@app.route('/admin-select', methods=['GET', 'POST'])
def admin_select():
    if not session.get('admin'):
        return redirect('/admin-login')
    if request.method == 'POST':
        selected_div = request.form.get('division', '')
        selected_cls = request.form.get('cls', '')
        return redirect(f'/admin-section?division={selected_div}&cls={selected_cls}')
    return render_template('main.html', page='admin-select')


@app.route('/admin-section', methods=['GET'])
def admin_section():
    if not session.get('admin'):
        return redirect('/admin-login')
    division = request.args.get('division')
    cls = request.args.get('cls')
    filtered = []

    if division or cls:
        users = load_users()
        for email, user in users.items():
            # support legacy keys by mirroring to short ones
            if 'div' not in user and 'division' in user:
                user['div'] = user.get('division')
            if 'cls' not in user and 'class_name' in user:
                user['cls'] = user.get('class_name')

            if division and user.get('div') != division:
                continue
            if cls and user.get('cls') != cls:
                continue
            user_copy = dict(user)
            user_copy['email'] = email
            filtered.append(user_copy)

    return render_template('main.html', page='admin', users=filtered)


def _ensure_marks(user):
    """Ensure marks structure exists for a user."""
    if 'marks' not in user or not isinstance(user['marks'], dict):
        user['marks'] = {}
    for term in ['first_term', 'second_term', 'final_term']:
        if term not in user['marks'] or not isinstance(user['marks'][term], dict):
            user['marks'][term] = {}
    return user['marks']


@app.route('/admin-marks', methods=['GET', 'POST'])
def admin_marks():
    if not session.get('admin'):
        return redirect('/admin-login')

    email = request.args.get('email') if request.method == 'GET' else request.form.get('email')
    if not email:
        return redirect('/admin-select')

    users = load_users()
    user = users.get(email)
    if not user:
        return render_template('main.html', page='admin-marks', error='Student not found.', student_email=email, marks={})

    marks = _ensure_marks(user)
    success = None

    subjects = ['eng', 'sl', 'phy', 'chem', 'math', 'cs']
    terms = ['first_term', 'second_term', 'final_term']

    if request.method == 'POST':
        for term in terms:
            term_marks = {}
            for subj in subjects:
                key = f"{term}_{subj}"
                term_marks[subj] = request.form.get(key, '').strip()
            marks[term] = term_marks

        users[email] = user
        save_users(users)
        success = 'Marks saved.'

    # reload marks to ensure template has persisted values
    current_marks = marks

    return render_template(
        'main.html',
        page='admin-marks',
        student=user,
        student_email=email,
        marks=current_marks,
        success=success
    )


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
