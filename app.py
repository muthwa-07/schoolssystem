
from flask import *
import logging
import pymysql
from datetime import datetime, timedelta
import re

# import the functions for hashing passwords and verifying the same
import functions

from logging.handlers import RotatingFileHandler
from cryptography.fernet import Fernet
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

# Create the Flask app before using it!
app = Flask(__name__)

# --- Logging setup ---
handler = RotatingFileHandler('error.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

# --- SQLAlchemy & Flask-Session Setup ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/CyberTestSystem'
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

db = SQLAlchemy(app)
app.config['SESSION_SQLALCHEMY'] = db
Session(app)

# --- Fernet Encryption Key ---
FERNET_KEY = b'mKDarWdfZnJGjGB6ENCMpxMIN-2pEZFvr8W0ohUwO3I='
fernet = Fernet(FERNET_KEY)

app.secret_key = "fhbcqhasbjfcncwasbhjZVcvwsdvcz"

# --- Log to Database ---
def log_to_db(level, message, endpoint=None, email=None):
    try:
        connection = pymysql.connect(host='localhost', user='root', password='', database='school_db')
        cursor = connection.cursor()

        encrypted_message = fernet.encrypt(message.encode())
        encrypted_endpoint = fernet.encrypt(endpoint.encode()) if endpoint else None
        encrypted_email = fernet.encrypt(email.encode()) if email else None

        cursor.execute(
            'INSERT INTO logs (log_level, log_message, endpoint, email) VALUES (%s, %s, %s, %s)',
            (level, encrypted_message, encrypted_endpoint, encrypted_email)
        )

        connection.commit()
        cursor.close()
        connection.close()
    except Exception as e:
        app.logger.error(f"MySQL logging failed: {e}")

# Password checker
def check_password_strength(password):
    # Minimum length check
    if len(password) < 8:
        return "Must be eight characters"

    elif not re.search("[a-z]", password):
        return "Must have at least one small letter"

    elif not re.search("[A-Z]", password):
        return "Must have at least one capital letter"

    elif not re.search("[0-9]", password):
        return "Must have at least one number"

    elif not re.search("[_@#$]", password):
        return "Must have at least one symbol"

    else:
        common_patterns = [
            r'(?i)password',
            r'(?i)123456',
            r'(?i)qwerty',
            r'(?i)admin',
            r'(?i)root',
            # Add more common patterns as needed
        ]
        
        for pattern in common_patterns:
            if re.search(pattern, password):
                return "Password too Simple"
        
        # If all criteria are met, return "Password correct"
        return "Password Correct - Strong Password"




# --- Automatically log every incoming request ---
@app.before_request
def log_request_info():
    try:
        level = 'INFO'
        message = f"Request made to {request.path} with method {request.method}"
        endpoint = request.path
        email = session.get('user_email', 'anonymous')

        log_to_db(level, message, endpoint, email)
    except Exception as e:
        app.logger.error(f"Failed to log request: {e}")

        app.logger.error(f"Failed to log request: {e}")

# --- Inactivity Logout --- 
INACTIVITY_TIMEOUT = 30 

@app.before_request
def check_inactivity():
    if 'userrole' in session:
        last_active = session.get('last_active')
        now = datetime.now()
        if last_active:
            try:
                last_active = datetime.strptime(last_active, "%Y-%m-%d %H:%M:%S.%f")
                if now - last_active > INACTIVITY_TIMEOUT:
                    email = session.get('useremail')
                    session.clear()
                    flash("You have been logged out due to inactivity.", "warning")
                    app.logger.info(f"{email} was logged out due to inactivity.")
                    log_to_db('INFO', 'User logged out due to inactivity.', endpoint='before_request', user_email=email)
                    return redirect('/login')
            except Exception as e:
                app.logger.error(f"Error parsing last_active timestamp: {e}")
                session.clear()
                return redirect('/login')
        session['last_active'] = str(now)





# --- Routes ---

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        fullname = request.form["fullname"]
        email = request.form['email']
        phone = request.form["phone"]
        password = request.form['password']
        role = "student"

        # Check password strength first
        password_check = check_password_strength(password)
        if password_check != "Password Correct - Strong Password":
            # Show error message and don't register
            return render_template("register.html", message=password_check)

        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
        cursor = connection.cursor()
        sql = "INSERT INTO users(fullname, email, phone, password, role) values(%s, %s, %s, %s, %s)"
        data = (fullname, email, phone, functions.hash_password_salt(password), role)
        cursor.execute(sql, data)
        connection.commit()
        cursor.close()
        connection.close()

        message = "User registered successfully"
        return render_template("register.html", message=message)


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        email = request.form["email"]
        password = request.form["password"]

        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
        cursor = connection.cursor()
        sql = "select * from users where email=%s"
        cursor.execute(sql, (email,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if user:
            db_password = user[3]
            role = user[5]
            fullname = user[1]

            if functions.verify_password_salt(db_password, password):
                session["user_name"] = fullname
                session["user_role"] = role
                session["user_id"] = user[0]
                session["user_email"] = email

                if role == "admin":
                    return redirect(url_for("admin_dashboard"))
                elif role == "teacher":
                    return redirect(url_for("teacher_dashboard"))
                else:
                    return redirect(url_for("student_dashboard"))
            else:
                return render_template("login.html", message="Incorrect Password")
        else:
            return render_template("login.html", message="Email not found")


@app.route("/student/dashboard")
def student_dashboard():
    if session.get("user_role") == "student":
        return render_template("student_dashboard.html", name=session.get("user_name"))
    return redirect(url_for("login"))


@app.route("/teacher/dashboard")
def teacher_dashboard():
    if session.get("user_role") != "teacher":
        return redirect(url_for('login'))

    connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
    cursor = connection.cursor()
    cursor.execute("select user_id from users where email=%s", (session.get("user_email"),))
    teacher = cursor.fetchone()

    if not teacher:
        cursor.close()
        connection.close()
        return "Teacher not Found"

    teacher_id = teacher[0]

    cursor.execute("select title, description, due_date, posted_at from assignments where teacher_id = %s order by posted_at DESC", (teacher_id,))
    assignments = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template("teacher_dashboard.html", name=session.get("user_name"), assignments=assignments)


@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("user_role") == "admin":
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
        cursor = connection.cursor()
        cursor.execute("select user_id, fullname, email, phone, role from users")
        users = cursor.fetchall()
        cursor.close()
        connection.close()

        return render_template("admin_dashboard.html", name=session.get("user_name"), users=users)
    return redirect(url_for("login"))


@app.route("/admin/user/<int:user_id>/edit", methods=["GET"])
def edit_user(user_id):
    if session.get("user_role") == "admin":
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
        cursor = connection.cursor()
        cursor.execute("select user_id, fullname, email, phone, role from users where user_id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        return render_template("edit_user.html", user=user)
    return redirect(url_for("login"))


@app.route("/admin/user/<int:user_id>/update", methods=["POST"])
def update_user(user_id):
    if session.get("user_role") == "admin":
        fullname = request.form["fullname"]
        email = request.form["email"]
        phone = request.form["phone"]
        role = request.form["role"]

        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
        cursor = connection.cursor()
        sql = "update users set fullname=%s , email=%s , phone=%s, role=%s where user_id=%s"
        data = (fullname, email, phone, role, user_id)
        cursor.execute(sql, data)
        connection.commit()
        cursor.close()
        connection.close()

        return redirect(url_for('admin_dashboard'))
    return redirect(url_for("login"))


@app.route("/teacher/assignments/create", methods=["GET", "POST"])
def create_assignment():
    if session.get("user_role") != "teacher":
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        due_date = request.form["due_date"]

        teacher_email = session.get("user_email")

        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
        cursor = connection.cursor()
        cursor.execute("SELECT user_id FROM users WHERE email=%s", (teacher_email,))
        teacher = cursor.fetchone()

        if teacher:
            teacher_id = teacher[0]
            sql = "INSERT INTO assignments (title, description, due_date, teacher_id) VALUES (%s, %s, %s, %s)"
            data = (title, description, due_date, teacher_id)
            cursor.execute(sql, data)
            connection.commit()
            cursor.close()
            connection.close()
            return redirect(url_for("teacher_dashboard"))
        else:
            cursor.close()
            connection.close()
            return "Teacher not found"

    return render_template("create_assignment.html")


@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    if session.get("user_role") != "admin":
        return redirect(url_for("login"))

    connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
    cursor = connection.cursor()
    sql = "DELETE FROM users WHERE user_id = %s"
    data = (user_id,)
    cursor.execute(sql, data)
    connection.commit()
    cursor.close()
    connection.close()

    return redirect(url_for("admin_dashboard"))


@app.route("/student/assignments", methods=["POST", "GET"])
def student_assignments():
    if session.get("user_role") != "student":
        return redirect(url_for("login"))

    connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
    cursor = connection.cursor()
    sql = "SELECT title, description, due_date, posted_at FROM assignments ORDER BY posted_at DESC"
    cursor.execute(sql)
    assignments = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template("student_assignments.html", assignments=assignments)


@app.route("/logs")
def view_logs():
    if 'user_role' not in session or session['user_role'] != 'admin':
        return redirect('/register')

    verified_time_str = session.get('logs_verified')
    if not verified_time_str:
        return redirect('/logs-auth')

    try:
        verified_time = datetime.strptime(verified_time_str, "%Y-%m-%d %H:%M:%S.%f")
        if datetime.now() - verified_time > timedelta(minutes=5):
            session.pop('logs_verified', None)
            return redirect('/logs-auth')
    except Exception as e:
        app.logger.warning(f"logs_verified parsing error: {e}")
        session.pop('logs_verified', None)
        return redirect('/logs-auth')

    try:
        connection = pymysql.connect(host='localhost', user='root', password='', database='school_db')
        cursor = connection.cursor()
        cursor.execute("SELECT id, log_level, log_message, endpoint, email, created_at FROM logs ORDER BY created_at DESC")
        rows = cursor.fetchall()

        logs = []
        for row in rows:
            try:
                logs.append({
                    'id': row[0],
                    'level': row[1],
                    'message': fernet.decrypt(row[2]).decode(),
                    'endpoint': fernet.decrypt(row[3]).decode() if row[3] else '',
                    'email': fernet.decrypt(row[4]).decode() if row[4] else '',
                    'created_at': row[5].strftime('%Y-%m-%d %H:%M:%S')
                })
            except Exception as e:
                logs.append({
                    'id': row[0],
                    'level': row[1],
                    'message': '[Decryption Error]',
                    'endpoint': '[Decryption Error]',
                    'email': '[Decryption Error]',
                    'created_at': row[5].strftime('%Y-%m-%d %H:%M:%S')
                })
                app.logger.warning(f"Decryption failed for log ID {row[0]}: {e}")

        cursor.close()
        connection.close()
        return render_template("logs.html", logs=logs)

    except Exception as e:
        app.logger.error(f"Failed to load logs: {e}")
        return render_template("logs.html", error="Could not load logs.")


@app.route('/logs-auth', methods=['GET', 'POST'])
def logs_auth():
    if session.get('user_role') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        password = request.form.get('password')

        # You can define a fixed password here, or better, verify against the admin's real password
        ADMIN_LOGS_PASSWORD = "supersecretlogs"

        if password == ADMIN_LOGS_PASSWORD:
            # Mark logs as verified with current timestamp
            session['logs_verified'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            return redirect(url_for('view_logs'))
        else:
            return render_template('logs-auth.html', error="Incorrect password")

    return render_template('logs-auth.html')


@app.route('/test-logs')
def test_logs():
    logs = [
        {'level': 'INFO', 'message': 'Test log 1', 'endpoint': '/test', 'email': 'user@example.com', 'created_at': '2025-07-27 12:00:00'},
        {'level': 'ERROR', 'message': 'Test log 2', 'endpoint': '/error', 'email': 'admin@example.com', 'created_at': '2025-07-27 13:00:00'},
    ]
    return render_template('logs.html', logs=logs)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
