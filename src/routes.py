from flask import render_template, request, redirect, url_for, flash, send_file, send_from_directory
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from sqlalchemy import false
from src.forms import LoginForm
from src.management import NbgraderManager
import webbrowser
import os
from src.models import User, Course, Section, Calification, CourseMembers
from src import app, db
from werkzeug.utils import secure_filename


#Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_current_User(id):
    return User.query.filter_by(id=id).first() 


db.drop_all()
db.create_all()

# manually added users
Teacher = User(name = "Profesor 1", username = "Teacher1", password = "1234", is_teacher = True)
Student1 = User(name = "Alberto", username = "Student1", password = "1234")
Student2 = User(name = "Pablo", username = "Student2", password = "1234")
db.session.add(Teacher)
db.session.add(Student1)
db.session.add(Student2)
db.session.commit()

course = Course(teacher_id = Teacher.id, name = "Curso de Python", description = "Curso básico de python" )
db.session.add(course)
db.session.commit()

section1 = Section(course_id = course.id, name = "Introduccion a Python", content_name = "T_Introduccion.ipynb", task_name = "EV_Introduccion")
section2 = Section(course_id = course.id, name = "Funciones en Python", content_name = "T_Funciones.ipynb", task_name = "EV_Funciones")

db.session.add(section1)
db.session.add(section2)
db.session.commit()

student_enroll1 = CourseMembers(course_id = course.id, student_id = Student1.id)
student_enroll2 = CourseMembers(course_id = course.id, student_id = Student2.id)
db.session.add(student_enroll1)
db.session.add(student_enroll2)
db.session.commit()

# ROUTES

@app.route('/login',methods=["GET", "POST"])
def login():

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if user.password == form.password.data:
                login_user(user)
                if user.is_teacher:
                    return redirect(url_for('teacher'))
                return redirect(url_for('student'))
        flash('usuario no registrado')
        return redirect(url_for('login'))

    return render_template("login.html", form = form)

@app.route('/logout',methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/teacher',methods=["GET", "POST"])
@login_required
def teacher():
    # TEST DE APERTURA DE NOTEBOOKS CON JUPYTER DESDE LA PAGINA PRINCIPAL DEL MAESTRO
    if request.method == 'POST':
        if request.form.get('action1') == 'RUN NOTEBOOK':
            #subprocess.Popen("jupyter notebook --ip='0.0.0.0' --port=8888")
            os.system("jupyter notebook --ip='0.0.0.0' --no-browser --allow-root --port=8888 &")
            #time.sleep(4)
            #webbrowser.open_new_tab("http://127.0.0.1:8888/notebooks/Curso%20Python%20V.0.ipynb")
            #webbrowser.open_new_tab("https://www.google.com/")
        if request.form.get('action2') == 'STOP NOTEBOOK':
            os.system("pkill -f -1 jupyter*")
            #subprocess.Popen("jupyter notebook stop 8888")

        if request.form.get('action3') == 'OPENTAB':
            webbrowser.open_new_tab("https://www.google.com/")
            #subprocess.Popen("jupyter notebook stop 8888")
    return render_template("teacher.html")

@app.route('/student',methods=["GET", "POST"])
@login_required
def student():
    if request.method == 'POST':
        return None
    user = get_current_User(current_user.get_id())
    return render_template("student.html", name = user.name)


@app.route('/student/courses',methods=["GET"])
@login_required
def student_courses():
    if request.method == 'POST':
        return None
    user = get_current_User(current_user.get_id())
    return render_template("student/courses.html", name = user.name, courses = get_student_courses(user.id))



# LISTA DE TODOS LOS CURSOS DE UN ALUMNO
def get_student_courses(student_id):
    courses = []
    relationships = CourseMembers.query.filter_by(student_id = student_id).all()
    for relationship in relationships:
        courses.append(Course.query.filter_by(id = relationship.course_id).first())
    return courses



@app.route('/student/courses/<string:course>',methods=["GET", "POST"])
@login_required
def student_course(course):

    user = get_current_User(current_user.get_id())

    if request.method == 'POST':
        if request.files:
            file = request.files['file']
            task = request.form.get('task')
            section = request.form.get('section')
            notebook = task + ".ipynb"
            if file.filename != notebook:
                flash('Debe seleccionar la tarea correspondiente a este sección: ' + notebook)
                return(redirect(request.url))
            else:
                preventive = Calification.query.filter_by(student_id=user.id,task_name=task).first()
                if preventive:
                    flash("Tarea entregada previamente")
                    return(redirect(request.url))
                flash("Su tarea ha sido enviada")
                path = "courses/" + course + "/submitted/" + user.name + "/" + task 
                file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),path ,secure_filename(file.filename)))
                manager = NbgraderManager(course)
                score = manager.grade(task,user.name)
                calification = Calification(student_id = user.id, section_id = section, task_name = task, value = score)
                db.session.add(calification)
                db.session.commit()
                manager.closeDB()
                

    
    current_course = Course.query.filter_by(name = course).first()
    sections = get_sections_data(current_course.id, user.id)
    return render_template("student/course.html", course = course, name = user.name, sections = sections)

def get_sections_data(course_id, student_id):
    sections = Section.query.filter_by(course_id =course_id).all()
    califications = Calification.query.filter_by(student_id = student_id).all()
    sections_data = []
    for section in sections:
        flag = "False"
        for calification in califications:
            if calification.section_id == section.id:
                flag = "True"
                break

        data_list = [section,flag]
        sections_data.append(data_list)

    return sections_data



@app.route('/download_content/<string:course>/<string:filename>')
def download_content(course,filename):
    path = "courses/" + course + "/content"
    return send_from_directory(path, filename, as_attachment=True)

@app.route('/download_task/<string:course>/<string:filename>')
def download_task(course,filename):
    path = "courses/" + course + "/release/" + filename
    notebook = filename + ".ipynb"
    return send_from_directory(path, notebook, as_attachment=True)

@app.route('/student/courses/<string:course>/<string:username>',methods=["GET"])
@login_required
def student_course_califications(course, username):
    current_course = Course.query.filter_by(name = course).first()
    user = get_current_User(current_user.get_id())
    sections = Section.query.filter_by(course_id = current_course.id).all()
    califications = []
    for section in sections:
        calification = Calification.query.filter_by(student_id=user.id, section_id=section.id).first()
        if calification:
            tmp_list = [section.name,calification]
            califications.append(tmp_list)
    return render_template("student/course_califications.html", course = course, name = user.name, califications = califications)

@app.route('/student/califications',methods=["GET"])
@login_required
def student_califications():
    user = get_current_User(current_user.get_id())
    courses = get_student_courses(user.id)
    califications = []
    for course in courses:
        sections = Section.query.filter_by(course_id = course.id).all()
        for section in sections:
            calification = Calification.query.filter_by(student_id=user.id, section_id=section.id).first()
            if calification:
                tmp_list = [course.name, section.name,calification]
                califications.append(tmp_list)
    return render_template("student/califications.html", name = user.name, califications = califications)