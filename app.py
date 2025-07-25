from flask import *

import pymysql

# import the functions for hashing passwords and verifying the same
import functions


# create a new application based on flask
app = Flask(__name__)


























# below is the register route
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

        # establish a connection to the db
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")

        # create a cursor that enables you to execute sql
        cursor = connection.cursor()

        # structure the sql query for insert
        sql = "INSERT INTO users(fullname, email, phone, password, role) values(%s, %s, %s, %s, %s)"


        # put the data into a tuple
        data = (fullname, email, phone, functions.hash_password_salt(password), role)

        # by use of the cursor, execute the query
        cursor.execute(sql, data)

        # commit the changes into the db
        connection.commit()

        message = "User registered successfully"

        # if succesfull render a message back to the person who has registered
        return render_template("register.html", message = message)


app.secret_key = "fhbcqhasbjfcncwasbhjZVcvwsdvcz"













@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        email = request.form["email"]
        password = request.form["password"]

         # establish a connection to the db
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")

        # create a cursor that enables you to execute sql
        cursor = connection.cursor()

        # structure a query for login
        sql = "select * from users where email=%s"

        # use the cursor to execute the sql
        cursor.execute(sql, (email,))

        # if the details are correct, put them into a users variable
        user = cursor.fetchone()

        print(user)

        if user:
            db_password = user[3]
            role = user[5]
            fullname = user[1]

            # verify the hashed password
            if functions.verify_password_salt(db_password, password):
                session["user_name"] = fullname
                session["user_role"] = role
                session["user_id"]=user[0]
                session["user_email"]=email


                # based on the role redirect a person to a given dashboard
                if role == "admin":
                    return redirect(url_for("admin_dashboard"))
                elif role == "teacher":
                    return redirect(url_for("teacher_dashboard"))
                else:
                    return redirect(url_for("student_dashboard"))
            else: 
                return render_template("login.html", message = "Incorrect Password")
        else:
            return render_template("login.html", message = "Email not found")

        













    
# route for the student dashboard
@app.route("/student/dashboard")
def student_dashboard():
    if session.get("user_role") == "student":
        return render_template("student_dashboard.html", name= session.get("user_name"))
    return redirect(url_for("login"))
















# Teacher dashboard
@app.route("/teacher/dashboard")
def teacher_dashboard():
    if session.get("user_role") != "teacher":
        return redirect(url_for('login'))
    # establish a connection to the db
    connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")

    cursor = connection.cursor()

    # get the current teacher id
    cursor.execute("select user_id from users where email=%s", (session.get("user_email"),))
    teacher = cursor.fetchone()

    if not teacher:
        return "Teacher not Found"
   
    teacher_id = teacher[0]

    cursor.execute("select title, description, due_date, posted_at from assignments where teacher_id = %s order by posted_at DESC", (teacher_id,))

    assignments = cursor.fetchall()

    return render_template("teacher_dashboard.html", name=session.get("user_name"), asssignments = assignments)

 
    












# route to the admin dashboard
@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("user_role") == "admin":
        # establish a connection to the db
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")

        cursor = connection.cursor()
        cursor.execute("select user_id, fullname, email, phone, role from users")

        users = cursor.fetchall()

        return render_template("admin_dashboard.html", name= session.get("user_name"), users= users)
    return redirect(url_for("login"))














# Edit user route

@app.route("/admin/user/<int:user_id>/edit", methods=["GET"])
def edit_user(user_id):
    if session.get("user_role") == "admin":
        # establish a connection to the db
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")

        cursor = connection.cursor()
        cursor.execute("select user_id, fullname, email, phone, role from users where user_id = %s", (user_id, ))
        user = cursor.fetchone()
        return render_template("edit_user.html", user = user)
    
    return redirect(url_for("login"))


# update route to update th user details
@app.route("/admin/user/<int:user_id>/update" , methods=["POST"])
def update_user(user_id):
    if session.get("user_role") == "admin":
        fullname = request.form["fullname"]
        email = request.form["email"]
        phone= request.form["phone"]
        role = request.form["role"]

        # establish a connection to the db
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")

        cursor = connection.cursor()

        sql ="update users set fullname=%s , email=%s , phone=%s, role=%s where user_id=%s "
        data = (fullname, email , phone, role , user_id)

        cursor.execute(sql,data)

        connection.commit()

        return redirect(url_for('admin_dashboard'))
    return redirect(url_for("login"))





















# ass route
@app.route("/teacher/assignments/create", methods=["GET", "POST"])
def create_assignment():
    if session.get("user_role") != "teacher":
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        due_date = request.form["due_date"]

        # Get teacher ID from session (assuming you store user_id after login)
        teacher_email = session.get("user_email")

        # Connect to DB to fetch teacher ID
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
            return redirect(url_for("teacher_dashboard"))
        else:
            return "Teacher not found"

    return render_template("create_assignment.html")

















# Delete route
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

    # After deleting, redirect back to the admin dashboard or show a message
    return redirect(url_for("admin_dashboard"))















# Student route to view assignment
@app.route("/student/assignments" ,methods=["POST","GET"])
def student_assignments():
    if session.get("user_role") != "student":
        return redirect(url_for("login"))

    connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")
    cursor = connection.cursor()

    # Assuming you want to show all assignments:
    sql = "SELECT title, description, due_date, posted_at FROM assignments ORDER BY posted_at DESC"
    cursor.execute(sql)
    assignments = cursor.fetchall()

    return render_template("student_assignments.html", assignments=assignments)


        


        
    
    





# logout Route
@app.route("/logout")
def logout():

    session.clear()
    return redirect(url_for("login"))


# run the application on a server
app.run(debug=True)