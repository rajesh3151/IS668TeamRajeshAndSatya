
from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, LoginManager, UserMixin, logout_user, login_required,current_user
from werkzeug.security import check_password_hash#,generate_password_hash
from datetime import datetime
#from flask_migrate import Migrate

app = Flask(__name__)
app.config["DEBUG"] = True

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="IS668Grade",
    password="mysql123",
    hostname="IS668Grade.mysql.pythonanywhere-services.com",
    databasename="IS668Grade$default",
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
#migrate = Migrate(app, db)
app.secret_key = "lksandfonodowdvvnonv"
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.username

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(username=user_id).first()

class Assignment(db.Model):

    __tablename__ = "assignments"

    assignmentid = db.Column(db.Integer, primary_key=True)
    assignmenttitle = db.Column(db.String(350))
    duedate = db.Column(db.Date)
    dateassigned = db.Column(db.Date)
    maxscore = db.Column(db.DECIMAL(5,2))
    comments = db.Column(db.String(4096))
    classid = db.Column(db.String(10))

class Student(db.Model):

    __tablename__ = "students"

    studentid = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(128))
    lastname = db.Column(db.String(128))
    email = db.Column(db.String(128))
    major = db.Column(db.String(128))
    classid = db.Column(db.String(10))

class Gradebook(db.Model):

    __tablename__ = "gradebooks"

    id = db.Column(db.Integer, primary_key=True)
    studentid = db.Column(db.Integer, db.ForeignKey('students.studentid'))
    assignmentid = db.Column(db.Integer, db.ForeignKey('assignments.assignmentid'))
    assignmentgrade = db.Column(db.DECIMAL(5,2))
    comments = db.Column(db.String(4096))
    submiton = db.Column(db.Date)
    student = db.relationship("Student", backref="gradebooks")
    assignment = db.relationship("Assignment", backref="gradebooks")

def get_final_score(finalscore):
    if finalscore>=97:
        finalGrade = 'A+'
    elif 93<=finalscore<97:
        finalGrade = 'A'
    elif 90<=finalscore<93:
        finalGrade = 'A-'
    elif 87<=finalscore<90:
        finalGrade = 'B+'
    elif 83<=finalscore<87:
        finalGrade = 'B'
    elif 80<=finalscore<83:
        finalGrade = 'B-'
    elif 77<=finalscore<80:
        finalGrade = 'C+'
    elif 73<=finalscore<77:
        finalGrade = 'C'
    elif 70<=finalscore<73:
        finalGrade = 'C-'
    elif 67<=finalscore<70:
        finalGrade = 'D+'
    elif 63<=finalscore<67:
        finalGrade = 'D'
    elif 60<=finalscore<63:
        finalGrade = 'D-'
    else:
        finalGrade = 'F'
    return finalGrade

def get_final_grade(studentID):
    gradebooks = Gradebook.query.filter_by(studentid=studentID).all()
    assignments = Assignment.query.all()
    totalmaxscore = 0
    totalscore = 0
    for assignment in assignments:
        totalmaxscore = totalmaxscore + assignment.maxscore
    for gradebook in gradebooks:
        totalscore = totalscore + gradebook.assignmentgrade
    finalscore = ( totalscore * 100 ) / totalmaxscore
    return get_final_score(finalscore)

###############################################################################
### LOGIN / LOGOUT / WELCOME
###############################################################################
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login_page_2.html", error=False)

    user = load_user(request.form["username"])
    if user is None:
        return render_template("login_page_2.html", error=True)

    if not user.check_password(request.form["password"]):
        return render_template("login_page_2.html", error=True)

    login_user(user)
    return redirect(url_for('welcome'))

@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/welcome", methods=["GET", "POST"])
@login_required
def welcome():
    #if not current_user.is_authenticated:
        return render_template("welcome_page.html")

###############################################################################
### STUDENTS
###############################################################################
@app.route('/students', methods=["GET"])
@login_required
def students():
    students = Student.query.all()
    return render_template('student_page.html', students=students, get_final_grade=get_final_grade )

@app.route('/add_student/', methods=["GET","POST"])
@login_required
def add_student():
    if request.method == "GET":
        return render_template("add_student.html")
    elif request.method == "POST":
        studentID = request.form.get("StudentID")
        if studentID != None:
            studentUpdate = Student.query.filter_by(studentid=studentID).first()
            studentUpdate.firstname = request.form.get("fname")
            studentUpdate.lastname  = request.form.get("lname")
            studentUpdate.major     = request.form.get("major")
            studentUpdate.email     = request.form.get("email")
            studentUpdate.classid   = request.form.get("classid")
        else:
            student = Student(
                firstname   = request.form["fname"],
                lastname    = request.form["lname"],
                major       = request.form["major"],
                email       = request.form["email"],
                classid     = request.form["classid"],
            )
            db.session.add(student)

        #db.session.add(student)
        db.session.commit()
        return redirect (url_for('students'))

@app.route('/edit_student/', methods=["POST"])
@login_required
def edit_student():
    student = Student.query.filter_by(studentid=request.form["StudentID"] ).first()
    return render_template("add_student.html", student=student )

@app.route('/delete_student/', methods=["POST"])
def delete_student():
	Gradebook.query.filter_by(studentid=request.form["StudentID"] ).delete()
	Student.query.filter_by(studentid=request.form["StudentID"] ).delete()
	db.session.commit()
	return redirect (url_for('students'))

###############################################################################
### ASSIGNMENTS
###############################################################################
@app.route('/assignments', methods=["GET"])
@login_required
def assignments():
    assignments = Assignment.query.all()
    return render_template('assignment_page.html', assignments=assignments )

@app.route('/add_assignment/', methods=["GET","POST"])
@login_required
def add_assignment():
    if request.method == "GET":
        return render_template("add_assignment.html")
    elif request.method == "POST":
        assignmentID = request.form.get("AssignmentID")

        if assignmentID != None:
            assignmentUpdate = Assignment.query.filter_by(assignmentid=assignmentID).first()
            assignmentUpdate.assignmenttitle = request.form.get("title")
            assignmentUpdate.duedate         = datetime.strptime(request.form.get("duedate"), '%Y-%m-%d').date()
            assignmentUpdate.dateassigned    = datetime.strptime(request.form.get("assigndate"), '%Y-%m-%d').date()
            assignmentUpdate.maxscore        = request.form.get("maxscore")
            assignmentUpdate.comments        = request.form.get("comments")
            assignmentUpdate.classid         = request.form.get("classid")
        else:
            assignment = Assignment(
                assignmenttitle = request.form["title"],
                duedate         = datetime.strptime(request.form.get("duedate"), '%Y-%m-%d').date(),
                dateassigned    = datetime.strptime(request.form.get("assigndate"), '%Y-%m-%d').date(),
                maxscore        = request.form["maxscore"],
                comments        = request.form["comments"],
                classid         = request.form["classid"],
            )
            db.session.add(assignment)
        db.session.commit()
        return redirect (url_for('assignments'))

@app.route('/edit_assignment/', methods=["POST"])
@login_required
def edit_assignment():
    assignment = Assignment.query.filter_by(assignmentid=request.form["AssignmentID"] ).first()
    return render_template("add_assignment.html", assignment=assignment )

@app.route('/delete_assignment/', methods=["POST"])
@login_required
def delete_assignment():
	Gradebook.query.filter_by(assignmentid=request.form["AssignmentID"] ).delete()
	Assignment.query.filter_by(assignmentid=request.form["AssignmentID"] ).delete()
	db.session.commit()
	return redirect (url_for('assignments'))


###############################################################################
### GRADES
###############################################################################
@app.route('/grade_student/', methods=["GET","POST"])
@login_required
def grade_student():
    student = Student.query.filter_by(studentid=request.form["StudentID"] ).first()
    assignments = Assignment.query.all()
    gradebooks   = Gradebook.query.filter_by(studentid=request.form["StudentID"] ).all()

    finalscore = 0
    for gradebook in gradebooks:
        finalscore = finalscore + gradebook.assignmentgrade

    finalGrade = get_final_score(finalscore)

    return render_template('student_gradebook.html', student=student, assignments=assignments, gradebooks=gradebooks,finalscore=finalscore,finalGrade=finalGrade)

@app.route('/grade_assignment/', methods=["GET","POST"])
@login_required
def grade_assignment():
    assignment   = Assignment.query.filter_by(assignmentid=request.form["AssignmentID"] ).first()
    students     = Student.query.all()
    gradebooks   = Gradebook.query.filter_by(assignmentid=request.form["AssignmentID"] ).all()
    return render_template('assignment_gradebook.html', students=students, assignment=assignment, gradebooks=gradebooks )

@app.route('/update_grades/', methods=["POST"])
@login_required
def update_grades():
    ids = request.form["GradeID"].split('_')
    gradetype  = request.form["GradeBook"]
    gradebook  = Gradebook.query.filter_by(assignmentid=ids[0],studentid=ids[1] ).first()
    assignment = Assignment.query.filter_by(assignmentid=ids[0] ).first()
    student    = Student.query.filter_by(studentid=ids[1] ).first()
    return render_template('update_grade.html', student=student, assignment=assignment, gradebook=gradebook,gradetype=gradetype)

@app.route('/save_grades/', methods=["POST"])
@login_required
def save_grades():
    GradeID     = request.form["GradeID"]
    GradeType   = request.form["GradeType"]
    if GradeID != '':
        gradebookUpdate = Gradebook.query.filter_by(id=GradeID).first()
        gradebookUpdate.assignmentid    = request.form.get("AssignmentID")
        gradebookUpdate.studentid       = request.form.get("StudentID")
        gradebookUpdate.assignmentgrade = request.form.get("actscore")
        gradebookUpdate.submiton        = datetime.strptime(request.form.get("submiton"), '%Y-%m-%d').date()
        gradebookUpdate.comments        = request.form.get("comments")
        db.session.commit()
    else:
        gradebookUpdate = Gradebook(studentid       = request.form.get("StudentID"),
                                    assignmentid    = request.form.get("AssignmentID"),
                                    assignmentgrade = request.form.get("actscore"),
                                    comments        = request.form.get("comments"),
                                    submiton        = datetime.strptime(request.form.get("submiton"), '%Y-%m-%d').date(),
                                    )
        db.session.add(gradebookUpdate)
    db.session.commit()

    if GradeType == "STUDENTS":
        #return redirect(url_for('grade_student'))
        student     = Student.query.filter_by(studentid=request.form.get("StudentID")).first()
        assignments = Assignment.query.all()
        gradebooks  = Gradebook.query.filter_by(studentid=request.form.get("StudentID")).all()
        return render_template('student_gradebook.html', student=student, assignments=assignments, gradebooks=gradebooks)
    else:
        #return redirect(url_for('grade_assignment'))
        students     = Student.query.all()
        assignment   = Assignment.query.filter_by(assignmentid=request.form["AssignmentID"] ).first()
        gradebooks   = Gradebook.query.filter_by(assignmentid=request.form["AssignmentID"] ).all()
        return render_template('assignment_gradebook.html', students=students, assignment=assignment, gradebooks=gradebooks )

###############################################################################
###############################################################################



# TODO: yet to display the students content with an aggregate grade in an html.
#provide a link to click on student name to display all the assignments for a given student
@app.route('/gradebook/all', methods=["GET"])
@login_required
def gradebook():
    user = User.query.all()
    assignments = Assignment.query.all()
    students = Student.query.all()
    gradebook = Gradebook.query.all()
    return render_template('gradebook_page.html', students=students, assignments=assignments, user=user, gradebook=gradebook)



