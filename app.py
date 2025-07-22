from flask import *
import pymysql
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
        data = fullname,email, phone, password, role

        # execute query using cursor
        cursor.execute(sql,data)

        # commit changes
        connection.commit()

        message="User registerd succesfully"

    #    return message
        return render_template("register.html", message=message)
    


@app.route("/login", methods=["POST","GET"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    else:
        email = request.form["email"]
        password= request.form["password"]

        # establish connection
        connection = pymysql.connect(host="localhost", password="",user="root", database="school_db" )

        # create a cursor
        cursor = connection.cursor()

        # SQL
        sql = "SELECT * FROM users WHERE email=%s AND password=%s"

        # tuple
        data = (email,password)

        # cursoe
        cursor.execute(data,sql)

        # if details are correct put them in users variable
        user = cursor.fetchone()

        if user:
            return render_template("login.html", message="Sucesfull")
        
        else:
            return render_template("login.html", message="Failed")
        





# run the app
app.run(debug=True)