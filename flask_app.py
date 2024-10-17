import os
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session, current_app
from flask_session import Session
from functools import wraps
from flask_mail import Mail, Message
from dotenv import load_dotenv
import pymysql
import yaml

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Get the directory of the current file
dir_path = os.path.dirname(os.path.realpath(__file__))

# Construct the full path to db.yaml
db_yaml_path = os.path.join(dir_path, 'db.yaml')

# Load database configuration from db.yaml
with open(db_yaml_path, 'r') as yaml_file:
    db = yaml.safe_load(yaml_file)

def get_db_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST'),      # e.g., 'db.yourprovider.com'
        user=os.getenv('DB_USER'),      # e.g., 'your_username'
        password=os.getenv('DB_PASSWORD'),  # e.g., 'your_password'
        db=os.getenv('DB_NAME')          # e.g., 'your_database'
    )
# Initialize MySQL


# Configure session
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'myiqinsight@gmail.com'
app.config['MAIL_PASSWORD'] = EMAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = 'myiqinsight@gmail.com'
app.config['MAIL_MAX_EMAILS'] = 10

mail = Mail(app)



def require_test_started(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_app.logger.info(f"Session contents: {session}")
        
        # Check if we're on the first question
        if request.path == '/question1':
            if 'user_age' not in session or 'user_email' not in session:
                flash("Please provide your age and email to start the test")
                return redirect("/question1")
        else:
            # For all other questions, require start_time to be set
            if 'start_time' not in session:
                flash("Please start the test from the beginning")
                return redirect("/")
        
        return f(*args, **kwargs)
    return decorated_function
'''
def require_previous_question(question_number):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            last_question = session.get("last_question", 0)

            # Special case for question 20 submission
            if question_number == 20 and request.method == "POST":
                return f(*args, **kwargs)

            # Check if trying to access a future question
            if question_number > last_question + 1:
                flash(f"Please complete question {last_question + 1} first")
                return redirect(f"/question{last_question + 1}")

            return f(*args, **kwargs)
        return decorated_function
    return decorator
'''
# Question difficulty mapping
question_difficulties = {
    "question1": 3,
    "question2": 2,
    "question3": 3,
    "question4": 2,
    "question5": 1,
    "question6": 1,
    "question7": 1,
    "question8": 1,
    "question9": 2,
    "question10": 1,
    "question11": 1,
    "question12": 2,
    "question13": 3,
    "question14": 1,
    "question15": 1,
    "question16": 1,
    "question17": 2,
    "question18": 2,
    "question19": 1,
    "question20": 1
}

questions_and_answers = {
    "question1": "Himself",
    "question2": "Some birds are cats",
    "question3": "Pick from the 'both' box",
    "question4": "11:00 AM",
    "question5": "John",
    "question6": "9",
    "question7": "Eating",
    "question8": "Shoe",
    "question9": "Sentence",
    "question10": "Winter",
    "question11": "32",
    "question12": "3 hours",
    "question13": "66 times",
    "question14": "$35",
    "question15": "D",
    "question16": "B",
    "question17": "F",
    "question18": "A",
    "question19": "B",
    "question20": "A"
}

@app.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy-policy.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    name = request.form['name']
    email = request.form['email']
    subject = request.form['subject']
    message_body = request.form['message']

    # Create the message
    msg = Message(subject=f"New Query from {name}: {subject}",
                  sender=email,
                  recipients=['myiqinsight@gmail.com'])

    # Format the email body
    msg.body = f"""
    Name: {name}
    Email: {email}

    Message:
    {message_body}
    """

    try:
        mail.send(msg)  # Send the email
        flash('Your message has been sent successfully!', 'success')
    except Exception as e:
        flash('Error sending your message. Please try again later.', 'danger')
        print(f"Mail error: {e}")

    return redirect('/contact')

def calculate_iq(correct_answers, time_taken_minutes, age):
    # Calculate IQ score based on test performance, time taken, and age
    if not correct_answers:
        return 0, 40  # Minimum score

    if time_taken_minutes < 0 or time_taken_minutes > 60:
        time_taken_minutes = 60  # Cap at 60 minutes

    correct_by_difficulty = {1: 0, 2: 0, 3: 0}
    for question in correct_answers:
        difficulty = question_difficulties[question]
        correct_by_difficulty[difficulty] += 1

    base_score = sum(
        difficulty * count
        for difficulty, count in correct_by_difficulty.items()
    )

    if time_taken_minutes < 5:
        base_score += 8
    elif time_taken_minutes < 10:
        base_score += 5

    max_possible_base = sum(question_difficulties.values())
    max_possible_score = max_possible_base + 8

    percentage_score = (base_score / max_possible_score) * 100

    age_adjustment = {
        range(6, 11): 1.1,
        range(11, 16): 1.05,
        range(16, 21): 1.02,
        range(21, 61): 1.0,
        range(61, 81): 0.98,
    }

    adjustment = 1.0
    for age_range, factor in age_adjustment.items():
        if age in age_range:
            adjustment = factor
            break

    iq_score = 100 + ((percentage_score - 50) * 0.6 * adjustment)
    final_iq = max(40, min(160, round(iq_score)))

    return base_score, final_iq

@app.route("/")
def index():
    # Initialize the database table
    if "points" not in session:
        session["points"] = 0
    return render_template("index.html")

@app.route("/iq-test")
def iq_test():
    return redirect("/age")

@app.route('/age', methods=['GET', 'POST'])
def age():
    if request.method == 'POST':
        age = request.form.get("age")
        email = request.form.get("email")
        
        # Check if both age and email are provided
        if not age or not email:
            flash("Please provide both age and email.")
            return redirect("/question1")
        
        # Initialize database connection
        connection = get_db_connection()
        cur = connection.cursor()
        cur.execute("INSERT INTO users(email, age) VALUES (%s, %s)", (email, age))
        connection.commit()
        cur.close()
        connection.close()
        
        # Set session variables
        session['user_age'] = age
        session['user_email'] = email
        session['start_time'] = datetime.now().isoformat()
        session['last_question'] = 0
        session['correct_answers'] = []  # Initialize the correct answers list

        current_app.logger.info(f"Age route: Setting session - age: {age}, email: {email}")

        return redirect('/question1')
    
    return render_template('age.html')

@app.route('/question1', methods=['GET', 'POST'])
@require_test_started
@require_previous_question(1)
def question1():
    if request.method == "POST":
        age = session.get('user_age')
        email = session.get('user_email')
        
        current_app.logger.info(f"Question1 route: Session contains - age: {age}, email: {email}")
        user_answer = request.form.get("answer")
        correct_answer = questions_and_answers["question1"]
        if user_answer == correct_answer:
            session["correct_answers"].append("question1")
        session["last_question"] = 1
        return redirect("/question2")

    return render_template('question1.html')

@app.route('/question2', methods=['GET', 'POST'])
@require_test_started
@require_previous_question(2)
def question2():
    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = questions_and_answers["question2"]
        if user_answer == correct_answer:
            session["correct_answers"].append("question2")
        session["last_question"] = 2
        return redirect("/question3")

    return render_template('question2.html')

@app.route('/question3', methods=['GET', 'POST'])
@require_test_started
@require_previous_question(3)
def question3():
    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = questions_and_answers["question3"]
        if user_answer == correct_answer:
           session["correct_answers"].append("question3")
        session["last_question"] = 3
        return redirect("/question4")

    return render_template('question3.html')

@app.route('/question4', methods=['GET', 'POST'])
@require_test_started
@require_previous_question(4)
def question4():
    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = questions_and_answers["question4"]
        if user_answer == correct_answer:
            session["correct_answers"].append("question4")
        session["last_question"] = 4
        return redirect("/question5")

    return render_template('question4.html')

@app.route('/question5', methods=['GET', 'POST'])
@require_test_started
@require_previous_question(5)
def question5():
    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = questions_and_answers["question5"]
        if user_answer == correct_answer:
            session["correct_answers"].append("question5")
        session["last_question"] = 5
        return redirect("/question6")

    return render_template('question5.html')

@app.route('/question6', methods=['GET', 'POST'])
@require_test_started
@require_previous_question(6)
def question6():
    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = questions_and_answers["question6"]
        if user_answer == correct_answer:
            session["correct_answers"].append("question6")
        session["last_question"] = 6
        return redirect("/question7")

    return render_template('question6.html')


@app.route('/question7', methods=['GET', 'POST'])
@require_test_started
@require_previous_question(7)
def question7():
    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = questions_and_answers["question7"]
        if user_answer == correct_answer:
            session["correct_answers"].append("question7")
        session["last_question"] = 7
        return redirect("/question8")

    return render_template('question7.html')





@app.route('/question8', methods=['GET', 'POST'])
@require_test_started
@require_previous_question(8)
def question8():
    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = questions_and_answers["question8"]
        if user_answer == correct_answer:
            session["correct_answers"].append("question8")
        session["last_question"] = 8
        return redirect("/question9")

    return render_template('question8.html')





@app.route('/question9', methods=['GET', 'POST'])
@require_test_started
@require_previous_question(9)
def question9():
    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = questions_and_answers["question9"]
        if user_answer == correct_answer:
            session["correct_answers"].append("question9")
        session["last_question"] = 9
        return redirect("/question10")

    return render_template('question9.html')




@app.route('/question10', methods=['GET', 'POST'])
@require_test_started
@require_previous_question(10)
def question10():
    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = questions_and_answers["question10"]
        if user_answer == correct_answer:
            session["correct_answers"].append("question10")
        session["last_question"] = 10
        return redirect("/question11")

    return render_template('question10.html')



@app.route('/question11', methods=['GET', 'POST'])
@require_test_started
@require_previous_question(11)
def question11():
    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = questions_and_answers["question11"]
        if user_answer == correct_answer:
            session["correct_answers"].append("question11")
        session["last_question"] = 11
        return redirect("/question12")
    return render_template('question11.html')




@app.route('/question12', methods=['GET', 'POST'])
@require_test_started
@require_previous_question(12)
def question12():
    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = questions_and_answers["question12"]
        if user_answer == correct_answer:
            session["correct_answers"].append("question12")
        session["last_question"] = 12
        return redirect("/question13")
    return render_template('question12.html')





@app.route('/question13', methods=['GET', 'POST'])
@require_test_started
@require_previous_question(13)
def question13():
    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = questions_and_answers["question13"]
        if user_answer == correct_answer:
            session["correct_answers"].append("question13")
        session["last_question"] = 13
        return redirect("/question14")
    return render_template('question13.html')



@app.route('/question14', methods=['GET', 'POST'])
@require_test_started
@require_previous_question(14)
def question14():
    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = questions_and_answers["question14"]
        if user_answer == correct_answer:
           session["correct_answers"].append("question14")
        session["last_question"] = 14
        return redirect("/question15")
    return render_template('question14.html')





@app.route('/question15', methods=['GET', 'POST'])
@require_test_started
@require_previous_question(15)
def question15():
    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = questions_and_answers["question15"]
        if user_answer == correct_answer:
            session["correct_answers"].append("question15")
        session["last_question"] = 15
        return redirect("/question16")
    return render_template('question15.html')




@app.route('/question16', methods=['GET', 'POST'])
@require_test_started
@require_previous_question(16)
def question16():
    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = questions_and_answers["question16"]
        if user_answer == correct_answer:
            session["correct_answers"].append("question16")
        session["last_question"] = 16
        return redirect("/question17")
    return render_template('question16.html')



@app.route('/question17', methods=['GET', 'POST'])
@require_test_started
@require_previous_question(17)
def question17():
    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = questions_and_answers["question17"]
        if user_answer == correct_answer:
            session["correct_answers"].append("question17")
        session["last_question"] = 17
        return redirect("/question18")
    return render_template('question17.html')





@app.route('/question18', methods=['GET', 'POST'])
@require_test_started
@require_previous_question(18)
def question18():
    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = questions_and_answers["question18"]
        if user_answer == correct_answer:
            session["correct_answers"].append("question18")
        session["last_question"] = 18
        return redirect("/question19")
    return render_template('question18.html')



@app.route('/question19', methods=['GET', 'POST'])
@require_test_started
@require_previous_question(19)
def question19():
    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = questions_and_answers["question19"]
        if user_answer == correct_answer:
            session["correct_answers"].append("question19")
        session["last_question"] = 19
        return redirect("/question20")
    return render_template('question19.html')




@app.route('/question20', methods=['GET', 'POST'])
@require_test_started
@require_previous_question(20)
def question20():
    if request.method == "POST":
        user_answer = request.form.get("answer")
        correct_answer = questions_and_answers["question20"]

        # Check if the answer is correct
        if user_answer == correct_answer:
            session["correct_answers"].append("question20")

        # Update last question
        session["last_question"] = 20

        # Calculate the IQ score and time taken
        end_time = datetime.now()
        time_taken = (end_time - session["start_time"]).total_seconds() / 60  # Time in minutes

        # Store time taken in session for final_score
        session["time_taken"] = time_taken

        # Calculate IQ score
        correct_answers = session.get("correct_answers", [])
        base_score, iq_score = calculate_iq(correct_answers, time_taken, session["user_age"])

        # Save the result to the database
        try:
            cur = mysql.connection.cursor()
            cur.execute("UPDATE users SET iq = %s, time_taken = %s WHERE email = %s", (iq_score, time_taken, session["user_email"]))
            mysql.connection.commit()
        except Exception as e:
            flash("There was an error saving your results. Please try again.")
            app.logger.error(f"Error updating database in question 20: {e}")
            return redirect("/")
        finally:
            cur.close()

        # Redirect to final score without clearing session data
        return redirect('/final-score')

    return render_template('question20.html')



@app.route('/final-score')
@require_test_started
def final_score():
    if session.get("last_question") != 20:
        flash("Please complete all questions first")
        return redirect(f"/question{session.get('last_question', 0) + 1}")

    if "time_taken" not in session:
        flash("Please complete the test first")
        return redirect("/")

    minutes_taken = session["time_taken"]

    final_points, iq = calculate_iq(
        session.get("correct_answers", []),
        minutes_taken,
        session["user_age"]
    )

    connection = get_db_connection()
    cur = connection.cursor()
    cur.execute("UPDATE users SET iq = %s, time_taken = %s WHERE email = %s", (iq, minutes_taken, session["user_email"]))
    connection.commit()
    cur.close()
    connection.close()

    session.clear()

    return render_template('final_score.html',
                           points=final_points,
                           iq=iq,
                           time_taken=minutes_taken)


if __name__ == "__main__":
    app.run(debug=True)
