
from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, LoginManager, UserMixin, logout_user, login_required
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

    id              = db.Column(db.Integer, primary_key=True)
    username        = db.Column(db.String(128))
    password_hash   = db.Column(db.String(128))

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.username

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(username=user_id).first()

class Class(db.Model):

    __tablename__ = "classes"

    classid = db.Column(db.String(10), primary_key=True)
    name    = db.Column(db.String(75))


class Assignment(db.Model):

    __tablename__ = "assignments"

    assignmentid    = db.Column(db.Integer, primary_key=True)
    assignmenttitle = db.Column(db.String(350))
    duedate         = db.Column(db.Date)
    dateassigned    = db.Column(db.Date)
    maxscore        = db.Column(db.DECIMAL(5,2))
    comments        = db.Column(db.String(4096))
    classid         = db.Column(db.String(10),db.ForeignKey('classes.classid'))

class Student(db.Model):

    __tablename__ = "students"

    studentid   = db.Column(db.Integer, primary_key=True)
    firstname   = db.Column(db.String(128))
    lastname    = db.Column(db.String(128))
    email       = db.Column(db.String(128))
    major       = db.Column(db.String(128))
    #classid     = db.Column(db.String(10))

class Gradebook(db.Model):

    __tablename__ = "gradebooks"

    id              = db.Column(db.Integer, primary_key=True)
    studentid       = db.Column(db.Integer, db.ForeignKey('students.studentid'))
    assignmentid    = db.Column(db.Integer, db.ForeignKey('assignments.assignmentid'))
    assignmentgrade = db.Column(db.DECIMAL(5,2))
    comments        = db.Column(db.String(4096))
    submiton        = db.Column(db.Date)
    student         = db.relationship("Student", backref="gradebooks")
    assignment      = db.relationship("Assignment", backref="gradebooks")

class ClassStudents(db.Model):

    __tablename__ = "class_students"

    classid     = db.Column(db.String(10), db.ForeignKey('classes.classid'),primary_key=True)
    studentid   = db.Column(db.Integer, primary_key=True)
    classes     = db.relationship('Class', backref='classes')

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

def get_final_grade(studentID,classID):
    gradebooks  = Gradebook.query.filter_by(studentid=studentID).all()
    assignments = Assignment.query.filter_by(classid=classID).all()
    totalmaxscore   = 0
    totalscore      = 0
    finalscore      = 0
    for assignment in assignments:
        totalmaxscore = totalmaxscore + assignment.maxscore
        for gradebook in gradebooks:
            if gradebook.assignmentid == assignment.assignmentid:
                totalscore = totalscore + gradebook.assignmentgrade
    if totalmaxscore > 0:
        finalscore = ( totalscore * 100 ) / totalmaxscore
    return get_final_score(finalscore)

def get_student_Count(classid):
    return ClassStudents.query.filter_by(classid=classid).count()

def get_assignment_Count(classid):
    return Assignment.query.filter_by(classid=classid).count()

def get_class_assigned(studentid,classid):
    if ClassStudents.query.filter_by(studentid=studentid,classid=classid).count() > 0:
        return "CHECKED"
    else:
        return ""

###############################################################################
### LOGIN / LOGOUT / WELCOME
###############################################################################
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", error=False)

    user = load_user(request.form["username"])
    if user is None:
        return render_template("login.html", error=True)

    if not user.check_password(request.form["password"]):
        return render_template("login.html", error=True)

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
### CLASS
###############################################################################

@app.route('/classes', methods=["GET"])
@login_required
def classes():
    classes = Class.query.all()
    return render_template('class_page.html', classes=classes,get_student_Count=get_student_Count,get_assignment_Count=get_assignment_Count)

@app.route('/add_class/', methods=["GET","POST"])
@login_required
def add_class():
    if request.method == "GET":
        return render_template("add_class.html")
    elif request.method == "POST":
        classaction = request.form.get("classaction")
        if classaction == 'EDIT':
            classUpdate = Class.query.filter_by(classid=request.form.get("classid")).first()
            classUpdate.name = request.form.get("classname")
        else:
            classAdd = Class(
                classid = request.form["classid"],
                name    = request.form["classname"],
            )
            db.session.add(classAdd)
        db.session.commit()
        return redirect (url_for('classes'))

@app.route('/edit_class/', methods=["POST"])
@login_required
def edit_class():
    classes = Class.query.filter_by(classid=request.form["classid"] ).first()
    return render_template("add_class.html", classes=classes )

@app.route('/delete_class/', methods=["POST"])
def delete_class():
	Class.query.filter_by(classid=request.form["classid"] ).delete()
	db.session.commit()
	return redirect (url_for('classes'))

@app.route('/assign_classes', methods=["GET","POST"])
@login_required
def assign_classes():

    selectedClasses = request.form.getlist('classid')
    checked = 0
    for i in range(len(selectedClasses)):
        if selectedClasses[i] != '-':
            checked = checked + 1
    if checked > 0:
        ClassStudents.query.filter_by(studentid=request.form["StudentID"]).delete()
        db.session.commit()
        for i in range(len(selectedClasses)):
            if selectedClasses[i] != '-':
                ClassStudent = ClassStudents(
                    classid   = selectedClasses[i],
                    studentid = request.form["StudentID"],
                )
                db.session.add(ClassStudent)
                db.session.commit()

    classes = Class.query.all()
    student = Student.query.filter_by(studentid=request.form["StudentID"] ).first()
    return render_template('assign_classes.html', classes=classes,student=student,get_class_assigned=get_class_assigned)

###############################################################################
### STUDENTS
###############################################################################
@app.route('/students', methods=["GET","POST"])
@login_required
def students():
    classes = Class.query.all()
    classid = request.form.get("classid")
    if classid == None:
        if request.args.get('classid') != '':
            if request.args.get('classid') != '-':
                classid = request.args.get('classid')
    if classid != None:
        if classid != '-':
            students = Student.query\
                .join(ClassStudents, Student.studentid==ClassStudents.studentid)\
                .add_columns(Student.studentid, Student.firstname,Student.lastname,Student.email,Student.major)\
                .filter(ClassStudents.classid == classid)
        else:
            students = Student.query.all()
    else:
        classid = classes[0].classid
        #students = Student.query.filter_by(classid=classid).all()
        students = Student.query\
            .join(ClassStudents, Student.studentid==ClassStudents.studentid)\
            .add_columns(Student.studentid, Student.firstname,Student.lastname,Student.email,Student.major)\
            .filter(ClassStudents.classid == classid)

    return render_template('student_page.html', students=students, classes=classes,classid=classid,get_final_grade=get_final_grade )

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
        else:
            student = Student(
                firstname   = request.form["fname"],
                lastname    = request.form["lname"],
                major       = request.form["major"],
                email       = request.form["email"],
            )
            db.session.add(student)

        db.session.commit()
        return redirect (url_for('students'))

@app.route('/edit_student/', methods=["POST"])
@login_required
def edit_student():
    student     = Student.query.filter_by(studentid=request.form["StudentID"] ).first()
    return render_template("add_student.html", student=student)

@app.route('/delete_student/', methods=["POST"])
def delete_student():
	ClassStudents.query.filter_by(studentid=request.form["StudentID"]).delete()
	Gradebook.query.filter_by(studentid=request.form["StudentID"] ).delete()
	Student.query.filter_by(studentid=request.form["StudentID"] ).delete()
	db.session.commit()
	return redirect (url_for('students'))

###############################################################################
### ASSIGNMENTS
###############################################################################
@app.route('/assignments', methods=["GET","POST"])
@login_required
def assignments():
    classid = request.form.get("classid")
    if classid == None:
        if request.args.get('classid') != '':
            classid = request.args.get('classid')
    classes = Class.query.all()
    if classid != None:
        assignments = Assignment.query.filter_by(classid=classid).all()
    else:
        if classes != None:
            assignments = Assignment.query.filter_by(classid=classes[0].classid).all()
    return render_template('assignment_page.html', assignments=assignments, classes=classes,classid=classid )

@app.route('/add_assignment/', methods=["GET","POST"])
@login_required
def add_assignment():
    if request.method == "GET":
        classes = Class.query.all()
        return render_template("add_assignment.html",classes=classes)
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
    assignment  = Assignment.query.filter_by(assignmentid=request.form["AssignmentID"] ).first()
    classes     = Class.query.all()
    return render_template("add_assignment.html", assignment=assignment,classes=classes )

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
    #classes  = Class.query.all()
    classes = Class.query\
                .join(ClassStudents, Class.classid==ClassStudents.classid)\
                .add_columns(Class.classid, Class.name)\
                .filter(ClassStudents.studentid == request.form["StudentID"])

    student     = Student.query.filter_by(studentid=request.form["StudentID"]).first()
    gradebooks  = Gradebook.query.filter_by(studentid=request.form["StudentID"]).all()
    assignments = Assignment.query.filter_by(classid=request.form["classid"]).all()

    finalscore = 0
    for assignment in assignments:
        for gradebook in gradebooks:
            if gradebook.assignmentid == assignment.assignmentid:
                finalscore = finalscore + gradebook.assignmentgrade
    finalGrade = get_final_grade(request.form["StudentID"],request.form["classid"])
    return render_template('student_gradebook.html', student=student, assignments=assignments, \
                            gradebooks=gradebooks,finalscore=finalscore,finalGrade=finalGrade, \
                            classes=classes)

@app.route('/grade_assignment/', methods=["GET","POST"])
@login_required
def grade_assignment():
    classes      = Class.query.filter_by(classid=request.form["classid"] ).first()
    assignment   = Assignment.query.filter_by(assignmentid=request.form["AssignmentID"] ).first()
    #students     = Student.query.filter_by(classid=request.form["classid"] ).all()
    students = Student.query\
        .join(ClassStudents, Student.studentid==ClassStudents.studentid)\
        .add_columns(Student.studentid, Student.firstname,Student.lastname,Student.email,Student.major)\
        .filter(ClassStudents.classid == request.form["classid"])
    gradebooks   = Gradebook.query.filter_by(assignmentid=request.form["AssignmentID"] ).all()
    return render_template('assignment_gradebook.html', students=students, assignment=assignment, gradebooks=gradebooks,classes=classes )

@app.route('/update_grades/', methods=["POST"])
@login_required
def update_grades():
    ids = request.form["GradeID"].split('_')
    gradetype  = request.form["GradeBook"]
    gradebook  = Gradebook.query.filter_by(assignmentid=ids[0],studentid=ids[1] ).first()
    assignment = Assignment.query.filter_by(assignmentid=ids[0] ).first()
    student    = Student.query.filter_by(studentid=ids[1] ).first()
    classes    = Class.query.filter_by(classid=request.form["classid"] ).first()
    return render_template('update_grade.html', student=student, assignment=assignment, \
                            gradebook=gradebook,gradetype=gradetype,classes=classes)

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
        #classes  = Class.query.all()
        classes = Class.query\
                .join(ClassStudents, Class.classid==ClassStudents.classid)\
                .add_columns(Class.classid, Class.name)\
                .filter(ClassStudents.studentid == request.form["StudentID"])
        student     = Student.query.filter_by(studentid=request.form["StudentID"]).first()
        gradebooks  = Gradebook.query.filter_by(studentid=request.form["StudentID"]).all()
        assignments = Assignment.query.filter_by(classid=request.form["classid"]).all()
        finalscore = 0
        for assignment in assignments:
            for gradebook in gradebooks:
                if gradebook.assignmentid == assignment.assignmentid:
                    finalscore = finalscore + gradebook.assignmentgrade
        #finalGrade = get_final_score(finalscore)
        finalGrade = get_final_grade(request.form["StudentID"],request.form["classid"])
        return render_template('student_gradebook.html', student=student, assignments=assignments, \
                                gradebooks=gradebooks,finalscore=finalscore,finalGrade=finalGrade, \
                                classes=classes)
    else:
        classes      = Class.query.filter_by(classid=request.form["classid"] ).first()
        assignment   = Assignment.query.filter_by(assignmentid=request.form["AssignmentID"] ).first()
        #students     = Student.query.filter_by(classid=request.form["classid"] ).all()
        students = Student.query\
            .join(ClassStudents, Student.studentid==ClassStudents.studentid)\
            .add_columns(Student.studentid, Student.firstname,Student.lastname,Student.email,Student.major)\
            .filter(ClassStudents.classid == request.form["classid"])

        gradebooks   = Gradebook.query.filter_by(assignmentid=request.form["AssignmentID"] ).all()
        return render_template('assignment_gradebook.html', students=students, assignment=assignment, gradebooks=gradebooks,classes=classes )

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



