from crypt import methods
from flask import render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from sqlalchemy import false
from src.forms import LoginForm, ChagePasswordForm, CreateStudentForm
from src.management import NbgraderManager
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


db.drop_all()
db.create_all()

# manually added db rows
Teacher = User(name = "Profesor 1", username = "Teacher1", password = "1234", is_teacher = True)
Student1 = User(name = "Alberto", username = "Student1", password = "1234", first_login = True)
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
@app.route('/',methods=["GET"])
def index():
    return render_template("index.html")

@app.route('/login',methods=["GET", "POST"])
def login():

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if user.verify_password(form.password.data):
                login_user(user)
                if user.is_teacher:
                    return redirect(url_for('teacher'))
                if user.first_login:
                    return redirect(url_for('student_change_password'))
                return redirect(url_for('student'))
        flash('usuario no registrado')
        return redirect(url_for('login'))

    return render_template("login.html", form = form)

@app.route('/logout',methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/teacher',methods=["GET"])
@login_required
def teacher():
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        return render_template("teacher.html", name = user.name)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))


@app.route('/teacher/change_password',methods=["GET", "POST"])
@login_required
def teacher_change_password():
    if check_access("teacher"):
        form = ChagePasswordForm()
        user = get_current_User(current_user.get_id())
        if form.validate_on_submit():
            password = form.current_password.data
            new_password_1 = form.new_password_1.data
            new_password_2 = form.new_password_2.data
            if user.verify_password(password):
                if new_password_1 == new_password_2:
                    if new_password_1 != password:
                        user.change_password(new_password_1)
                        user.first_login = False
                        db.session.commit()
                        return redirect(url_for('logout'))
                    flash("La nueva contraseña no puede ser la misma a la actual")
                    return redirect(url_for('teacher_change_password'))
                flash("Datos erroneos")
                return redirect(url_for('teacher_change_password'))
            flash("Contraseña incorrecta")
            redirect(url_for('teacher_change_password'))
        return render_template("teacher/change_password.html", form = form)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))


@app.route('/teacher/students',methods=["GET"])
@login_required
def teacher_students():
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        students = get_teacher_students(user.id)
        return render_template("teacher/students.html", name = user.name, students = students)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))

@app.route('/teacher/create_student',methods=["GET"])
@login_required
def teacher_create_student():
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        form = CreateStudentForm()
        if form.validate_on_submit():
            None 
            #TODO
        return render_template("teacher/create_student.html", name = user.name, form = form)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))

@app.route('/teacher/students/<string:student>',methods=["GET"])
@login_required
def teacher_students_student(student):
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        student = User.query.filter_by(username = student).first()
        courses = get_student_courses(student.id)
        califications = get_student_califications(student, courses)
        return render_template("teacher/student.html", name = user.name, student = student.username, califications = califications)

    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))

@app.route('/student',methods=["GET"])
@login_required
def student():
    if check_access("student"):
        user = get_current_User(current_user.get_id())
        return render_template("student.html", name = user.name)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('teacher'))


@app.route('/student/courses',methods=["GET"])
@login_required
def student_courses():
    if check_access("student"):
        user = get_current_User(current_user.get_id())
        return render_template("student/courses.html", name = user.name, courses = get_student_courses(user.id))
    else:
        flash("Acceso no permitido")
        return redirect(url_for('teacher'))



@app.route('/student/courses/<string:course>',methods=["GET", "POST"])
@login_required
def student_course(course):
    if check_access("student"):
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
                    else:
                        flash("Su tarea ha sido enviada")
                        path = "courses/" + course + "/submitted/" + user.username + "/" + task 
                        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),path ,secure_filename(file.filename)))
                        manager = NbgraderManager(course)
                        score = manager.grade(task,user.username)
                        calification = Calification(student_id = user.id, section_id = section, task_name = task, value = score)
                        db.session.add(calification)
                        db.session.commit()
                        manager.closeDB()
                    
        current_course = Course.query.filter_by(name = course).first()
        sections = get_sections_data(current_course.id, user.id)
        return render_template("student/course.html", course = course, name = user.name, sections = sections)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('teacher'))



@app.route('/download_content/<string:course>/<string:filename>')
@login_required
def download_content(course,filename):
    if check_access("student"):
        path = "courses/" + course + "/content"
        return send_from_directory(path, filename, as_attachment=True)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('teacher'))

@app.route('/download_task/<string:course>/<string:filename>')
@login_required
def download_task(course,filename):
    if check_access("student"):
        path = "courses/" + course + "/release/" + filename
        notebook = filename + ".ipynb"
        return send_from_directory(path, notebook, as_attachment=True)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('teacher'))

@app.route('/student/courses/<string:course>/<string:username>',methods=["GET"])
@login_required
def student_course_califications(course, username):
    if check_access("student"):
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
    else:
        flash("Acceso no permitido")
        return redirect(url_for('teacher'))

@app.route('/student/califications',methods=["GET"])
@login_required
def student_califications():
    if check_access("student"):
        user = get_current_User(current_user.get_id())
        courses = get_student_courses(user.id)
        califications = get_student_califications(user, courses)
        return render_template("student/califications.html", name = user.name, califications = califications)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('teacher'))



@app.route('/student/change_password',methods=["GET", "POST"])
@login_required
def student_change_password():
    if check_access("student"):
        form = ChagePasswordForm()
        user = get_current_User(current_user.get_id())
        if form.validate_on_submit():
            password = form.current_password.data
            new_password_1 = form.new_password_1.data
            new_password_2 = form.new_password_2.data
            if user.verify_password(password):
                if new_password_1 == new_password_2:
                    if new_password_1 != password:
                        user.change_password(new_password_1)
                        user.first_login = False
                        db.session.commit()
                        return redirect(url_for('logout'))
                    flash("La nueva contraseña no puede ser la misma a la actual")
                    return redirect(url_for('student_change_password'))
                flash("Datos erroneos")
                return redirect(url_for('student_change_password'))
            flash("Contraseña incorrecta")
            redirect(url_for('student_change_password'))
        return render_template("student/change_password.html", form = form)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('teacher'))


# METODOS ADICIONALES DE FUNCIONAMIENTO

def get_current_User(id):
    return User.query.filter_by(id=id).first() 

# LISTA DE TODOS LOS CURSOS DE UN ALUMNO
def get_student_courses(student_id):
    courses = []
    relationships = CourseMembers.query.filter_by(student_id = student_id).all()
    for relationship in relationships:
        courses.append(Course.query.filter_by(id = relationship.course_id).first())
    return courses

def get_teacher_courses(teacher_id):
    return Course.query.filter_by(teacher_id = teacher_id).all()

def get_student_califications(user, courses):
    califications = []
    for course in courses:
            sections = Section.query.filter_by(course_id = course.id).all()
            for section in sections:
                calification = Calification.query.filter_by(student_id=user.id, section_id=section.id).first()
                if calification:
                    tmp_list = [course.name, section.name,calification]
                    califications.append(tmp_list)
    return califications



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


def check_access(user_type):
    user = get_current_User(current_user.get_id())
    if user_type == "teacher":
        if user.is_teacher:
            return True
        else:
            return False
    elif user_type == "student":
        if not user.is_teacher:
            return True
        else:
            return False
    
def get_teacher_students(teacher_id):
    courses = get_teacher_courses(teacher_id)
    relationships = []
    alumnos = []
    for course in courses:
        relationship = CourseMembers.query.filter_by(course_id=course.id).all()
        for relation in relationship:
            relationships.append(relation)
    for relationship_ in relationships:
        alumnos.append(User.query.filter_by(id = relationship_.student_id).first())
    return alumnos


# @app.route('/teacher',methods=["GET", "POST"])
# @login_required
# def teacher():
#     # TEST DE APERTURA DE NOTEBOOKS CON JUPYTER DESDE LA PAGINA PRINCIPAL DEL MAESTRO
#     if request.method == 'POST':
#         if request.form.get('action1') == 'RUN NOTEBOOK':
#             #subprocess.Popen("jupyter notebook --ip='0.0.0.0' --port=8888")
#             os.system("jupyter notebook --ip='0.0.0.0' --no-browser --allow-root --port=8888 &")
#             #time.sleep(4)
#             #webbrowser.open_new_tab("http://127.0.0.1:8888/notebooks/Curso%20Python%20V.0.ipynb")
#             #webbrowser.open_new_tab("https://www.google.com/")
#         if request.form.get('action2') == 'STOP NOTEBOOK':
#             os.system("pkill -f -1 jupyter*")
#             #subprocess.Popen("jupyter notebook stop 8888")

#         if request.form.get('action3') == 'OPENTAB':
#             webbrowser.open_new_tab("https://www.google.com/")
#             #subprocess.Popen("jupyter notebook stop 8888")
#     return render_template("teacher.html")
