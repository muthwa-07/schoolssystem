from flask import *
import pymysql


# import hashinf functions
import functions

# Create a new appl based on flask

app = Flask(__name__)

# Below is the register route
@app.route("/register", methods=["POST","GET"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    
    else:
        fullname = request.form["fullname"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        role = "student"

        # establish connection
        connection = pymysql.connect(host="localhost", password="",user="root", database="school_db" )

        # create a cursor
        cursor = connection.cursor()

        # structure SQL for insert
        sql = "INSERT INTO users(fullname, email, phone, password , role)  values(%s, %s, %s, %s, %s)"

        # Place data in tuple
        data = (fullname,email, phone, functions.hash_password_salt(password), role)

        # execute query using cursor
        cursor.execute(sql,data)

        # commit changes
        connection.commit()

        message="User registerd succesfully"

    #    return message
        return render_template("register.html", message=message)
    

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




# student dashboard
@app.route("/student/dashboard")
def student_dashboard():
     if session.get("user_role") == "student":
          return render_template("student_dashboard.html" ,name = session.get("user_name"))
     return redirect(url_for("login"))


# teacher route
@app.route("/teacher/dashboard")
def teacher_dashboard():
    if session.get("user_role") == "teacher":
        return render_template("teacher_dashboard.html" ,name = session.get("user_name"))
    return redirect(url_for("login"))




# admin rote dashboard
@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("user_role") == "admin":
         # establish a connection to the db
        connection = pymysql.connect(host="localhost", user="root", password="", database="school_db")

        cursor = connection.cursor()

        cursor.execute("select  user_id, fullname , email, phone ,role from users")

        users= cursor.fetchall()

        return render_template("admin_dashboard.html" , name = session.get("user_name") ,users=users)
    return redirect(url_for("login"))

# log out
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# run the app
app.run(debug=True)