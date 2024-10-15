import os
import random
import re
import smtplib
import subprocess
import tempfile
import time
import traceback
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pyodbc
from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   session, url_for)
from pymongo import MongoClient
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__, template_folder="templates")
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "your_secret_key_here"
)  # Use environment variable for secret key

psno = 0

# MongoDB setup
client = MongoClient(
    "mongodb+srv://vankyrs:rukHnjdLGabqQGnA@problestatement.ztrbltk.mongodb.net/?retryWrites=true&w=majority&appName=ProbleStatement"
)

#SQL Connection for state and city db
connections = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=LAPTOP-LENF5EL5\SQLEXPRESS;"
    "Database=state_city;"
    "Trusted_Connection=yes;"
)

#MonngoDB for Problem Statements
db = client["Problems"]
collection = db["Statements"]


#MongoDB for contest Details 
db2 = client["Contest"]
collection2 = db2["Contests"]

# SQL Server setup
connection_string = "Driver={ODBC Driver 17 for SQL Server};Server=RAMESH\\MSSQLSERVER02;Database=student;Trusted_Connection=yes;"

contests = collection2.find_one({})
psno = contests['psno']
problems = list(collection.find_one({}))

# Functions without any kind of routes enabled
def get_connect():
    return pyodbc.connect(connections)

def get_states():
    try:
        conn = get_connect()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT state_name FROM states")
        states = [row[0] for row in cursor.fetchall()]
        return states
    except Exception as e:
        print(f"Error fetching states : {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_cities(state):
    try:
        conn = get_connect()
        cursor = conn.cursor()
        cursor.execute("SELECT city_name FROM cities WHERE state_name = ?", (state,))
        cities = [row[0] for row in cursor.fetchall()]
        return cities
    except Exception as e:
        print(f"Error fetching cities : {e}")
        return[]
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Functions without any kind of routes enabled
def get_connection():
    return pyodbc.connect(connection_string)

def get_java_class_name(code):
    match = re.search(r'\bpublic\s+class\s+(\w+)', code)
    if match:
        return match.group(1)
    return None

# OTP Generation and Email Sending
def generate_otp(length=6):
    digits = "0123456789"
    otp = ''.join(random.choice(digits) for _ in range(length))
    return otp

def send_otp_email(to_email):
    from_email = "vijay.artiset1@gmail.com"
    password = "Vijay@2004"
    otp = generate_otp()
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    subject = "Your OTP Code"
    body = f"Your OTP code is {otp}. It is valid for 5 minutes."
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        print("OTP email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
    finally:
        server.quit()
    return otp, time.time()

def verify_otp(user_otp, sent_otp, sent_otp_time, expiration_time=300):
    current_time = time.time()
    if user_otp == sent_otp and (current_time - sent_otp_time) <= expiration_time:
        return True
    return False

# Route for main landing page no login included 
@app.route("/")
@app.route("/home")
def home():
    return render_template("landingpage.html")

# Route for login form
@app.route("/login")
def login():
    return render_template("login.html")

@app.route('/resetpass')
def resetpass():
    return render_template('resetpass.html')

@app.route('/send_reset_code', methods=['POST'])
def send_reset_code():
    email = request.form['email']
    otp, sent_otp_time = send_otp_email(email)
    session['otp'] = otp
    session['otp_time'] = sent_otp_time
    flash('Reset code sent to your email address.')
    return redirect(url_for('resetpass'))

@app.route('/handle_reset_code', methods=['POST'])
def handle_reset_code():
    user_otp = request.form['reset_code']
    sent_otp = session.get('otp')
    sent_otp_time = session.get('otp_time')
    if verify_otp(user_otp, sent_otp, sent_otp_time):
        flash('Reset code verified. Please proceed to reset your password.')
        return redirect(url_for('home'))
    else:
        flash('Invalid or expired reset code.')
        return redirect(url_for('resetpass'))

# Route for handling login logic
@app.route("/loginpage", methods=["POST", "GET"])
def loginpage():
    email = request.form.get("email")
    password = request.form.get("password")

    try:
        conn = get_connection()  # Assuming get_connection() retrieves your SQLite connection
        cursor = conn.cursor()

        # Use parameterized query to avoid SQL injection
        cursor.execute("SELECT * FROM Students WHERE EmailId = ?", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user[17], password):
            # Store user data in session
            session["user"] = {
                "fname": user[2],
                "lname": user[4],
                "email": user[5],
                "college": user[6],
                "mobile": user[7]
            }
            # Redirect to dashboard route with correct parameter name
            return redirect(url_for("dashboard", username=session["user"]["fname"]))
        else:
            flash("Invalid email or password. Please try again.")
            return redirect(url_for("login"))

    except Exception as e:
        flash(f"An error occurred: {str(e)}")
        return redirect(url_for("login"))

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
       
    return render_template("loginpage.html")

# Route for admin page
@app.route("/admin")
def admin():
    return render_template("admin.html")

# Route for dashboard displaying user details
@app.route("/dashboard/<username>")
def dashboard(username):
    if "user" in session:
        username = session["user"]
        contests = collection2.find_one({})
        return render_template("dashboard.html", username=username, contests = contests)
    else:
        flash("You need to login first.")
        return redirect(url_for("loginpage"))

# Route for code editor page
@app.route("/code/<contest>/<username>")
def code(contest, username):
    if "user" in session:
        try:
            contests = collection2.find_one({})
            psno = contests['psno']
            
            # Fetch the specific problem using psno
            problem = collection.find({})[psno]  # Modify this query as per your database schema
            print(problem)
            if problem:
                return render_template("index.html", user=session["user"], problem=problem)
            else:
                flash("Problem not found.")
                return render_template("index.html", user=session["user"], problem=None)
        
        except Exception as e:
            flash(f"An error occurred: {str(e)}")
            return render_template("index.html", user=session["user"], problem=None)
    
    else:
        flash("You are not logged in.")
        return redirect(url_for("login"))

@app.route("/contestreg")
def contestreg():
    return render_template("contestreg.html")

@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        conn = None
        cursor = None
        try:
            fullname = request.form.get("Fullname")
            namelist = list(fullname.split(" "))
            fname = namelist[0]
            mname = namelist[1:len(namelist) - 1]
            mname_str = " ".join(mname) if mname else None
            lname = namelist[-1]
            if lname == fname:
                lname = None 
            email = request.form.get("email")
            college = request.form.get("college")
            mobile = request.form.get("mobile")
            gender = request.form.get("gender")
            dob = request.form.get("dob")
            internship_duration = request.form.get("internshipDuration")
            internship_mode = request.form.get("internshipMode")
            home_state = request.form.get("homeState")
            home_city = request.form.get("homecity")
            current_location = request.form.get("Currentcity")
            alternate_mobile = request.form.get("AlternateMobile")
            alternate_email = request.form.get("AlternateEmail")
            password = request.form.get("inputPassword4")
            con_password = request.form.get("confirmPassword")
            password_hash = generate_password_hash(password)
            
            Primary_skill = request.form.get("Primary skill")
            Secondary_skill = request.form.get("Secondary Skill")
            optional_skill = request.form.get("optional Skill")
            
            specialization = request.form.get("Specialization")
            edu = request.form.get("level")
            course = request.form.get("Course")

            if password != con_password:
                flash("Password does not match.")
                return redirect(url_for("register"))

            # Validate if all necessary fields are present
            if not (fullname and email and college and mobile and gender and dob and internship_duration and internship_mode and password and con_password):
                flash("Please fill in all required fields.")
                return redirect(url_for("register"))

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT EmailId FROM Students WHERE EmailId = ?", (email,)
            )
            if cursor.fetchone():
                flash("Email already exists. Please use a different email.")
                return redirect(url_for("register"))

            cursor.execute(
                """
                INSERT INTO Students (Fullname, fname, mname, lname, EmailId, College, Mobile, Gender, DOB, InternshipDuration, InternshipMode, HomeState, HomeCity, CurrentLocation, AlternateMobile, AlternateEmail, Password, PrimarySkill, SecondarySkill, OptionalSkill, Specialization, Education, Course)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fullname,
                    fname,
                    mname_str,
                    lname,
                    email,
                    college,
                    mobile,
                    gender,
                    dob,
                    internship_duration,
                    internship_mode,
                    home_state,
                    home_city,
                    current_location,
                    alternate_mobile,
                    alternate_email,
                    password_hash,
                    Primary_skill,
                    Secondary_skill,
                    optional_skill,
                    specialization,
                    edu,
                    course
                ),
            )

            conn.commit()
            flash("You have registered successfully. Please login.")
            return redirect(url_for("login"))

        except Exception as e:
            flash(f"An error occurred: {str(e)}")
            return redirect(url_for("register"))

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template("register.html")

@app.route("/compile", methods=["POST"])
def compile_code():
    code = request.json.get("code")
    result = {"output": "", "error": ""}

    # Save the code to a temporary file
    with tempfile.NamedTemporaryFile(suffix=".java", delete=False) as temp_file:
        temp_file.write(code.encode("utf-8"))
        temp_file_path = temp_file.name

    try:
        # Compile the code
        compile_process = subprocess.run(
            ["javac", temp_file_path], capture_output=True, text=True
        )
        if compile_process.returncode != 0:
            result["error"] = compile_process.stderr
        else:
            # Get the Java class name from the code
            class_name = get_java_class_name(code)
            if class_name:
                # Run the compiled Java code
                run_process = subprocess.run(
                    ["java", "-cp", os.path.dirname(temp_file_path), class_name],
                    capture_output=True,
                    text=True,
                )
                if run_process.returncode != 0:
                    result["error"] = run_process.stderr
                else:
                    result["output"] = run_process.stdout
            else:
                result["error"] = "Could not determine Java class name."
    except Exception as e:
        result["error"] = str(e)
    finally:
        # Clean up the temporary file
        os.remove(temp_file_path)

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)

