from ast import Pass
from curses.ascii import US
import shutil
from flask import render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from pyparsing import removeQuotes
from requests import session
from src.forms import LoginForm, ChagePasswordForm, CreateStudentForm, CreateCourseForm
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
Student3 = User(name = "Pedro", username = "Student3", password = "1234")
db.session.add(Teacher)
db.session.add(Student1)
db.session.add(Student2)
db.session.add(Student3)
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
    user = get_current_User(current_user.get_id())
    if user.is_teacher:
        os.system("pkill -f -1 jupyter*")
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
                    flash("La nueva contraseña no puede ser la misma que la actual")
                    return redirect(url_for('teacher_change_password'))
                flash("Las contraseñas han de coincidir")
                return redirect(url_for('teacher_change_password'))
            flash("Contraseña incorrecta")
            redirect(url_for('teacher_change_password'))
        return render_template("teacher/change_password.html", form = form)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))


@app.route('/teacher/courses',methods=["GET"])
@login_required
def teacher_courses():
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        courses = Course.query.filter_by(teacher_id = user.id).all()
        return render_template("teacher/courses.html", name = user.name, courses = courses)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))

@app.route('/teacher/courses/<string:course>',methods=["GET"])
@login_required
def teacher_courses_course(course):
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        course = Course.query.filter_by(name = course).first()
        return render_template("teacher/course.html", name = user.name)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))

@app.route('/teacher/courses/<string:course>/students',methods=["GET"])
@login_required
def teacher_course_students(course):
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        course = Course.query.filter_by(name = course).first()
        students = User.query.filter_by(is_teacher = False).all()
        relationships = CourseMembers.query.filter_by(course_id = course.id).all()
        students_in = []
        students_out = []
        for student in students:
            flag = False
            for relationship in relationships:
                if relationship.student_id == student.id:
                    flag = True
            if flag:
                students_in.append(student)
            else:
                students_out.append(student)

        return render_template("teacher/course_students.html",course = course.name, name = user.name, students_in = students_in, students_out = students_out)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))

@app.route('/teacher/quick/<string:course>/<string:student>',methods=["GET"])
@login_required
def teacher_quick_student(course,student):
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        course = Course.query.filter_by(name = course).first()
        student = User.query.filter_by(username = student).first()
        relation = CourseMembers.query.filter_by(course_id = course.id, student_id = student.id).first()
        if not relation:
            flash('Este alumno ya habia sido eliminado del curso')
            return redirect(url_for("teacher_course_students",course = course.name)) 
        quick_from_course(course,student)
        flash("Alumno borrado del curso")
        return redirect(url_for("teacher_course_students",course = course.name))
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))


@app.route('/teacher/enrroll/<string:course>/<string:student>',methods=["GET"])
@login_required
def teacher_enrroll_student(course,student):
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        course = Course.query.filter_by(name = course).first()
        student = User.query.filter_by(username = student).first()
        relation = CourseMembers(course_id = course.id, student_id = student.id)
        try:
            db.session.add(relation)
            db.session.commit()
            manager = NbgraderManager(course.name)
            manager.add_student(student.username)
            manager.closeDB()
        except:
            db.session.rollback()
            flash("Alumno existente en el curso")
            return redirect(url_for("teacher_course_students",course = course.name))
        make_dir_submissions(course.name, student.username)
        flash("Alumno añadido al curso")
        return redirect(url_for("teacher_course_students",course = course.name))

    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))


@app.route('/teacher/create_course',methods=["GET", "POST"])
@login_required
def teacher_create_course():
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        form = CreateCourseForm()
        if form.validate_on_submit():
            name = form.name.data
            description = form.description.data
            try:
                course = Course(teacher_id = user.id, name = name, description = description)
                db.session.add(course)
                db.session.commit()
            except Exception:
                flash("Ya existe un curso con ese nombre")
                return redirect(url_for("teacher_courses"))
            else:
                path = "courses/" + name 
                path_ = "courses/base_course"
                source = os.path.join(os.path.abspath(os.path.dirname(__file__)), path_)
                destination = os.path.join(os.path.abspath(os.path.dirname(__file__)), path)
                shutil.copytree(source,destination)
                flash("Curso creado correctamente")
                return redirect(url_for("teacher_courses"))


        return render_template("teacher/create_course.html", name = user.name, form = form)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))



@app.route('/teacher/califications',methods=["GET"])
@login_required
def teacher_califications():
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        califications = get_teachers_califications(user.id)
        return render_template("teacher/califications.html", name = user.name, califications = califications)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))

@app.route('/teacher/students',methods=["GET"])
@login_required
def teacher_students():
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        enrrolled = get_teacher_students(user.id)
        return render_template("teacher/students.html", name = user.name, enrrolled = enrrolled)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))


@app.route('/delete_student/<string:student_id>')
@login_required
def delete_student(student_id):
    if check_access("teacher"):
        student = User.query.filter_by(id = student_id).first()
        courses = get_student_courses(student_id)
        relationships = CourseMembers.query.filter_by(student_id = student_id).all()
        califications = Calification.query.filter_by(student_id = student_id).all()
        for course in courses:
            path = "courses/" + course.name + "/submitted/" + student.username
            path_ = os.path.join(os.path.abspath(os.path.dirname(__file__)), path)
            shutil.rmtree(path_)
            manager = NbgraderManager(course.name)
            manager.remove_student(student.username)
            manager.closeDB()
        for relation in relationships:
            db.session.delete(relation)
        for calification in califications:
            db.session.delete(calification)
        db.session.delete(student)
        db.session.commit()
        return redirect(url_for('teacher_students'))
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))



@app.route('/teacher/create_student',methods=["GET","POST"])
@login_required
def teacher_create_student():
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        form = CreateStudentForm()
        if form.validate_on_submit():
            name = form.name.data
            username = form.username.data
            password1 = form.password.data
            password2 = form.confirm_password.data
            course_value = request.form.get("courses")
            if course_value != None:
                course = Course.query.filter_by(name = course_value).first()
                if password1 == password2:
                    try:
                        user = User(name = name, username = username, password = password1, first_login=True)
                        db.session.add(user)
                        db.session.commit()
                        relationship = CourseMembers(course_id = course.id, student_id = user.id)
                        db.session.add(relationship)
                        db.session.commit()
                        make_dir_submissions(course.name, user.username)
                        manager = NbgraderManager(course.name)
                        manager.add_student(user.username)
                        flash("Usuario creado correctamente")
                        return redirect(url_for('teacher_students'))
                    except Exception as e:
                        db.session.rollback()
                        flash("Usuario ya existente")
                else:
                    flash("Las contraseñas han de coincidir")
            else:
                flash("Debe seleccionar un curso")
        courses = get_teacher_courses(user.id)
        return render_template("teacher/create_student.html", name = user.name, form = form, courses = courses)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))

@app.route('/teacher/students/<string:student>',methods=["GET", "POST"])
@login_required
def teacher_students_student(student):
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        student = User.query.filter_by(username = student).first()
        if not student:
            return redirect(url_for("teacher_students"))
        if request.method == 'POST':
            return redirect(url_for('delete_student', student_id = student.id))
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

def get_course_sections(course):
    sections = []
    sections_ = Section.query.filter_by(course_id = course.id).all()
    for section in sections_:
        sections.append(section)
    return sections

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


def make_dir_submissions(course, username):
    path = "courses/" + course + "/submitted/" + username
    path_ = os.path.join(os.path.abspath(os.path.dirname(__file__)), path)
    os.mkdir(path_)
    course_ = Course.query.filter_by(name = course).first()
    sections = Section.query.filter_by(course_id = course_.id).all()
    for section in sections:
        s_path = path_ + "/" + section.task_name
        os.mkdir(s_path)


def get_teachers_califications(teacher_id):
    courses = Course.query.filter_by(teacher_id = teacher_id).all()
    final_califications = []
    for course in courses:
        sections = Section.query.filter_by(course_id = course.id).all()
        for section in sections:
            califications = Calification.query.filter_by(section_id = section.id).all()
            for calification in califications:
                user = User.query.filter_by(id = calification.student_id).first()
                tmp_list = [course.name, section.name, user.name, user.username, section.task_name, calification.value]
                final_califications.append(tmp_list)
    return final_califications


def quick_from_course(course,student):

        path = "courses/" + course.name + "/submitted/" + student.username
        path_ = os.path.join(os.path.abspath(os.path.dirname(__file__)), path)
        shutil.rmtree(path_)
        manager = NbgraderManager(course.name)
        manager.remove_student(student.username)
        manager.closeDB()

        relation = CourseMembers.query.filter_by(course_id = course.id, student_id = student.id).first()
        
        db.session.delete(relation)
        sections = get_course_sections(course)
        for section in sections:
            calification = Calification.query.filter_by(student_id = student.id, section_id = section.id).first()
            if calification:
                db.session.delete(calification)
        db.session.commit()


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
