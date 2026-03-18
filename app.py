from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import mysql.connector
from mysql.connector import Error
import hashlib
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'servicehub_secret_2026')

# ─── DB CONFIG ────────────────────────────────────────────────────────────────
DB_CONFIG = {
    'host':     os.environ.get('DB_HOST', 'localhost'),
    'user':     os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', '5450'),
    'database': os.environ.get('DB_NAME', 'service_hub'),
    'autocommit': True,
}

def get_db():
    """Return a fresh MySQL connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ─── AUTH DECORATORS ──────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html', user=session.get('username'))

# ── AUTH ──────────────────────────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        location = request.form.get('location', '').strip()
        mobile   = request.form.get('mobile', '').strip()

        if not all([name, username, password, location, mobile]):
            flash('All fields are required.', 'error')
            return render_template('register.html')

        db = get_db()
        if not db:
            flash('Database error. Please try again.', 'error')
            return render_template('register.html')

        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            flash('Username already taken.', 'error')
            cursor.close(); db.close()
            return render_template('register.html')

        cursor.execute(
            "INSERT INTO users (name, username, password, location, mobile) VALUES (%s,%s,%s,%s,%s)",
            (name, username, hash_password(password), location, mobile)
        )
        cursor.close(); db.close()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        db = get_db()
        if not db:
            flash('Database error.', 'error')
            return render_template('login.html')

        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE username = %s AND password = %s",
            (username, hash_password(password))
        )
        user = cursor.fetchone()
        cursor.close(); db.close()

        if user:
            session['user_id']  = user['id']
            session['username'] = user['username']
            session['name']     = user['name']
            flash(f"Welcome back, {user['name']}!", 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

# ── SERVICES ──────────────────────────────────────────────────────────────────

@app.route('/services')
def services():
    return render_template('services.html', user=session.get('username'))


@app.route('/workers')
def worker_list():
    profession = request.args.get('profession', '').strip()
    search     = request.args.get('search', '').strip()

    db = get_db()
    workers = []
    if db:
        cursor = db.cursor(dictionary=True)
        if profession:
            cursor.execute(
                "SELECT * FROM workers WHERE LOWER(profession) = LOWER(%s) ORDER BY experience DESC",
                (profession,)
            )
        elif search:
            cursor.execute(
                "SELECT * FROM workers WHERE LOWER(profession) LIKE LOWER(%s) OR LOWER(name) LIKE LOWER(%s) ORDER BY experience DESC",
                (f'%{search}%', f'%{search}%')
            )
        else:
            cursor.execute("SELECT * FROM workers ORDER BY experience DESC")
        workers = cursor.fetchall()
        cursor.close(); db.close()

    return render_template('worker_list.html',
                           workers=workers,
                           profession=profession,
                           user=session.get('username'))


@app.route('/worker/register', methods=['GET', 'POST'])
def worker_register():
    if request.method == 'POST':
        name       = request.form.get('name', '').strip()
        profession = request.form.get('profession', '').strip()
        experience = request.form.get('experience', '0')
        location   = request.form.get('location', '').strip()
        mobile     = request.form.get('mobile', '').strip()

        if not all([name, profession, experience, location, mobile]):
            flash('All fields are required.', 'error')
            return render_template('worker_register.html')

        db = get_db()
        if not db:
            flash('Database error.', 'error')
            return render_template('worker_register.html')

        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO workers (name, profession, experience, location, mobile) VALUES (%s,%s,%s,%s,%s)",
            (name, profession, int(experience), location, mobile)
        )
        cursor.close(); db.close()
        flash('Worker registered successfully!', 'success')
        return redirect(url_for('services'))

    return render_template('worker_register.html', user=session.get('username'))

# ── API (AJAX) ─────────────────────────────────────────────────────────────────

@app.route('/api/workers')
def api_workers():
    profession = request.args.get('profession', '').strip()
    db = get_db()
    if not db:
        return jsonify({'error': 'DB unavailable'}), 500

    cursor = db.cursor(dictionary=True)
    if profession:
        cursor.execute(
            "SELECT * FROM workers WHERE LOWER(profession) = LOWER(%s) ORDER BY experience DESC",
            (profession,)
        )
    else:
        cursor.execute("SELECT * FROM workers ORDER BY experience DESC")
    workers = cursor.fetchall()
    cursor.close(); db.close()
    return jsonify(workers)

# ─── PROFILE ──────────────────────────────────────────────────────────────────

@app.route('/profile')
@login_required
def profile():
    db = get_db()
    user = None
    if db:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        cursor.close(); db.close()
    return render_template('profile.html', user=user)

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
