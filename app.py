import os
import re
import subprocess
import tempfile
import traceback
from datetime import datetime

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


# print("This is psno:",psno, "This is contests:",contests, "This is problems:",problems)


#Functions without any kind of routes enabled
def get_connection():
    return pyodbc.connect(connection_string)

def get_java_class_name(code):
    match = re.search(r'\bpublic\s+class\s+(\w+)', code)
    if match:
        return match.group(1)
    return None

#Route for main landing page no login included 
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
    # Logic to send reset code to the email goes here
    flash('Reset code sent to your email address.')
    return redirect(url_for('resetpass'))

@app.route('/handle_reset_code', methods=['POST'])
def handle_reset_code():
    email = request.form['email']
    reset_code = request.form['reset_code']
    # Add your reset code verification logic here
    flash('Reset code verified. Please proceed to reset your password.')
    return redirect(url_for('home'))

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
                "SELECT EmailId, Mobile FROM Students WHERE EmailId = ? OR Mobile = ?",
                (email, mobile),
            )
            
            existing_user = cursor.fetchone()
            if existing_user:
                dbmail, dbmobile = existing_user
                if dbmail == email:
                    flash("A user is already registered with this E-Mail, please login.")
                if dbmobile == mobile:
                    flash("An account already exists with this phone number, please login")
                return redirect(url_for("register"))

            cursor.execute(
                "INSERT INTO Students (FirstName, MiddleName, LastName, EmailId, College, Mobile, Gender, DOB, InternshipDuration, InternshipMode, HomeState, HomeCity, CurrentLocation, AlternateMobile, AlternateEmail, password, FullName) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (fname, mname_str, lname, email, college, mobile, gender, dob, internship_duration, internship_mode, home_state, home_city, current_location, alternate_mobile, alternate_email, password_hash, fullname),
            )

            # Get the StudentID of the inserted student
            cursor.execute("SELECT SCOPE_IDENTITY()")
            student_id = cursor.fetchone()[0]

            cursor.execute(
                "INSERT INTO Education (StudentID, Level, Course, Specialization) VALUES (?, ?, ?, ?)",
                (student_id, edu, course, specialization),
            )
            
            cursor.execute(
                "INSERT INTO Skills (StudentID, Primary_Skill, Secondary_Skill, optional_Skill) VALUES (?, ?, ?, ?)",
                (student_id, Primary_skill, Secondary_skill, optional_skill),
            )

            cursor.execute("SELECT skills FROM def_skills")
            skill_list = cursor.fetchall()

            # Process the skill_list if needed
            skills = [skill[0] for skill in skill_list]
            
            conn.commit()
            flash("Registration successful. Please login.")
            return redirect(url_for("loginpage"))

        except Exception as e:
            if conn:
                conn.rollback()
            traceback.print_exc()  # Print the full traceback for debugging
            flash(f"An error occurred during registration: {str(e)}")
            return redirect(url_for("register"))

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # Pass the skill list to the template if you need it there
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT skills FROM def_skills")
    skill_list = cursor.fetchall()
    skills = [skill[0] for skill in skill_list]
    cursor.close()
    conn.close()
    
    return render_template("registration.html", skills=skills)



@app.route('/submit_problem', methods=['POST'])
def submit_problem():
    try:
        problem_statement = request.form["problem_statement"]
        description = request.form["description"]
        constraints = request.form["constraints"]
        test_inputs = request.form.getlist("test_input[]")
        expected_outputs = request.form.getlist("expected_output[]")
        
        # Construct the document to insert into MongoDB
        document = {
            "problem_statement": problem_statement,
            "description": description,
            "constraints": constraints,
            "test_cases": [
                {"input": test_input, "output": expected_output}
                for test_input, expected_output in zip(test_inputs, expected_outputs)
            ],
            
        }
        
        collection.insert_one(document)

        return redirect(url_for("home"))

    except Exception as e:
        return f"An error occurred: {str(e)}"



# # Logout section to close the user sessions
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# #Not te be changed, any changes will affect the working of code editor and will not show any output.

@app.route("/execute_code", methods=["POST"])
def execute_code():
    try:
        data = request.json
        code = data["code"]
        print(code)
        language = data["language"]
        user_input = data.get("input", "")
        print(user_input)
        if language == "python":
            # Write code to a temporary Python file
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
                temp_file.write(code.encode())
                temp_file.flush()  # Ensure all data is written to file
                temp_file_name = temp_file.name
                for i in temp_file:
                    print(i)
            # Execute the temporary Python file
            result = subprocess.run(
                ["python", temp_file_name],
                input=user_input,
                capture_output=True,
                text=True,
                timeout=25,
                shell=True
            )

            # Clean up temporary file
            os.remove(temp_file_name)
        
        elif language == "java":
            # Java execution remains unchanged from your original code
            class_name = get_java_class_name(code)  # Implement this function
            if not class_name:
                return jsonify({"error": "Unable to determine the class name from the Java code."})
            
            file_name = f"{class_name}.java"
            with open(file_name, "w") as file:
                file.write(code)
            
            compile_result = subprocess.run(
                ["javac", file_name],
                capture_output=True,
                text=True
            )
            if compile_result.returncode != 0:
                return jsonify({"error": compile_result.stderr.strip()})
            
            result = subprocess.run(
                ["java", class_name],
                input=user_input,
                capture_output=True,
                text=True,
                timeout=10,
                shell=False
            )
            os.remove(f"{class_name}.class")
            os.remove(file_name)
        
        else:
            return jsonify({"error": f"Unsupported language: {language}"})
        
        if result.returncode == 0:
            return jsonify({"output": result.stdout.strip()})
        else:
            return jsonify({"error": result.stderr.strip()})
    
    except KeyError as e:
        return jsonify({"error": f"KeyError: {str(e)}"})
    
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"CalledProcessError: {str(e)}"})
    
    except subprocess.TimeoutExpired as e:
        return jsonify({"error": f"TimeoutExpired: {str(e)}"})
    
    except Exception as e:
        return jsonify({"error": f"Exception: {str(e)}"})


@app.route("/check_code", methods=["POST"])
def check_code():
    try:
        data = request.json
        code = data["code"]
        language = data["language"]

        # Log incoming code and language
        app.logger.info(f"Received code for language: {language}")

        # Fetch psno from the contest collection
        contest = collection2.find_one({})
        if not contest:
            app.logger.error("No contest found in collection2")
            return jsonify({"error": "No contest found"})

        psno = contest.get('psno')
        if psno is None:
            app.logger.error("No psno found in contest")
            return jsonify({"error": "No psno found in contest"})

        app.logger.info(f"psno: {psno}")

        # Fetch the specific problem using psno from the statements collection
        problem = collection.find()[psno]
        if not problem:
            app.logger.error(f"No problem found with psno: {psno}")
            return jsonify({"error": f"No problem found with psno: {psno}"})

        # Log the problem details
        app.logger.info(f"Problem statement: {problem.get('problem_statement', 'No problem statement available')}")

        test_cases = problem.get("test_cases", [])
        if not test_cases:
            app.logger.error(f"No test cases found for problem with psno: {psno}")
            return jsonify({"error": f"No test cases found for problem with psno: {psno}"})

        results = []
        all_passed = True

        if language == "python":
            for index, test_case in enumerate(test_cases, start=1):
                cus_input = test_case.get("input", "").strip()
                expected_output = test_case.get("output", "").strip()
                result = execute_python(code, cus_input)
                actual_output = result["output"]
                error_message = result.get("error", None)

                if error_message:
                    results.append(f"Test Case {index}: Failed. Error: {error_message}")
                    all_passed = False
                elif actual_output == expected_output:
                    results.append(f"Test Case {index}: Passed")
                else:
                    results.append(f"Test Case {index}: Failed. Got: '{actual_output}', Expected: '{expected_output}'")
                    all_passed = False

        elif language == "java":
            for index, test_case in enumerate(test_cases, start=1):
                cus_input = test_case.get("input", "").strip()
                expected_output = test_case.get("output", "").strip()
                result = execute_java(code, cus_input)
                actual_output = result["output"]
                error_message = result.get("error", None)

                if error_message:
                    results.append(f"Test Case {index}: Failed. Error: {error_message}")
                    all_passed = False
                elif actual_output == expected_output:
                    results.append(f"Test Case {index}: Passed")
                else:
                    results.append(f"Test Case {index}: Failed. Got: '{actual_output}', Expected: '{expected_output}'")
                    all_passed = False

        else:
            return jsonify({"error": f"Unsupported language: {language}"})

        response = {"results": results}
        if all_passed:
            response["redirect"] = "/home"
        return jsonify(response)

    except KeyError as e:
        app.logger.error(f"KeyError: {str(e)}")
        return jsonify({"error": f"KeyError: {str(e)}"})

    except Exception as e:
        app.logger.error(f"Exception: {str(e)}")
        return jsonify({"error": f"Exception: {str(e)}"})


def execute_python(code, cus_input):
    temp_filename = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
            temp_filename = temp_file.name
            temp_file.write(code.encode())

        # Construct the command to run the Python script
        command = f"python {temp_filename}"

        # Run the command in a new shell environment
        result = subprocess.run(
            command, input=cus_input, capture_output=True, text=True, timeout=5, shell=True
        )

        output = result.stdout.strip()
        error = result.stderr.strip() if result.stderr else None

        return {"output": output, "error": error}

    except subprocess.CalledProcessError as e:
        return {"error": f"CalledProcessError: {str(e)}"}

    except subprocess.TimeoutExpired as e:
        return {"error": f"TimeoutExpired: {str(e)}"}

    except Exception as e:
        return {"error": f"Exception: {str(e)}"}

    finally:
        if temp_filename and os.path.exists(temp_filename):
            os.remove(temp_filename)

def execute_java(code, cus_input):
    java_filename = None
    class_filename = None
    try:
        class_name = get_java_class_name(code)  # Define this function

        if not class_name:
            return {"output": "", "error": "Unable to determine the class name from the Java code."}

        java_filename = f"{class_name}.java"
        class_filename = f"{class_name}.class"

        with open(java_filename, "w") as file:
            file.write(code)

        compile_command = ["javac", java_filename]
        compile_result = subprocess.run(
            compile_command, capture_output=True, text=True, timeout=5, shell=False
        )

        if compile_result.returncode != 0:
            return {"output": "", "error": f"Compilation Error: {compile_result.stderr.strip()}"}

        execution_command = ["java", class_name]
        result = subprocess.run(
            execution_command, input=cus_input, capture_output=True, text=True, timeout=5, shell=False
        )

        output = result.stdout.strip()
        error = result.stderr.strip() if result.stderr else None

        return {"output": output, "error": error}

    except subprocess.CalledProcessError as e:
        return {"output": "", "error": f"CalledProcessError: {str(e)}"}

    except subprocess.TimeoutExpired as e:
        return {"output": "", "error": f"TimeoutExpired: {str(e)}"}

    except Exception as e:
        return {"output": "", "error": f"Exception: {str(e)}"}

    finally:
        if java_filename and os.path.exists(java_filename):
            os.remove(java_filename)
        if class_filename and os.path.exists(class_filename):
            os.remove(class_filename)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
    

