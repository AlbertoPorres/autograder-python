import shutil
import time
from flask import render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from pyparsing import removeQuotes
from requests import session
import werkzeug
from src.forms import LoginForm, ChagePasswordForm, CreateStudentForm, CreateCourseForm
from src.management import NbgraderManager
import os
from src.models import User, Course, Section, Calification, CourseMembers, UnreleasedSection
from src import app, db
from werkzeug.utils import secure_filename
from pathlib import Path 

#Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
                    return redirect(url_for('change_password'))
                return redirect(url_for('student'))
        flash('usuario no registrado')
        return redirect(url_for('login'))

    return render_template("login.html", form = form, user = None)

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
        return render_template("teacher.html", user = user)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))


@app.route('/change_password',methods=["GET", "POST"])
@login_required
def change_password():
    
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
                    return redirect(url_for('change_password'))
                flash("Las contraseñas han de coincidir")
                return redirect(url_for('change_password'))
            flash("Contraseña incorrecta")
            redirect(url_for('change_password'))
        return render_template("change_password.html", user = user, form = form)



@app.route('/teacher/courses',methods=["GET"])
@login_required
def teacher_courses():
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        courses = Course.query.filter_by(teacher_id = user.id).all()
        return render_template("teacher/courses.html",user = user, courses = courses)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))

@app.route('/teacher/courses/<string:course>',methods=["GET"])
@login_required
def teacher_courses_course(course):
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        course = Course.query.filter_by(name = course).first()
        sections = get_course_sections(course)
        return render_template("teacher/course.html",  user = user, sections = sections, course = course)
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

        return render_template("teacher/course_students.html",course = course.name,  user = user, students_in = students_in, students_out = students_out)
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

        return render_template("teacher/create_course.html", user = user, form = form)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))


@app.route('/teacher/kernel-loader/<string:task>',methods=["GET"])
@login_required
def teacher_kernel_loader(task):
    if check_access("teacher"):
        time.sleep(5)
        user = get_current_User(current_user.get_id())
        section = UnreleasedSection.query.filter_by(task_name = task).first()
        if section:
            course = Course.query.filter_by(id = section.course_id).first()
            return render_template("teacher/kernel_loader.html",  user = user, task = task, course = course.name)
        else:
            os.system("pkill -f -1 jupyter*")
            return render_template("teacher/error_template.html")
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))

@app.route('/teacher/kernel-loader/',methods=["GET"])
@login_required
def teacher_kernel_error():
    if check_access("teacher"):
        flash("Algo salio mal")
        os.system("pkill -f -1 jupyter*")
        return render_template("teacher/error_template.html",  user = user)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))

@app.route('/teacher/<string:course>/create_section',methods=["GET", "POST"])
@login_required
def teacher_create_section(course):
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        course = Course.query.filter_by(name = course).first()
        if request.method == 'POST':
            
            try:
                # confirmacion de la tarea creada indirectamente
                request.form["confirm"]
                unreleased = UnreleasedSection.query.filter_by(teacher_id = user.id, course_id = course.id).all()
                for unrelease in unreleased:
                    section = Section(course_id = course.id, name = unrelease.name, content_name = unrelease.content_name, task_name = unrelease.task_name)
                    manager = NbgraderManager(course.name)
                    manager.create_assigment(section.task_name)
                    manager.closeDB()
                    db.session.add(section)
                    db.session.delete(unrelease)
                    db.session.commit()
                
                os.system("pkill -f -1 jupyter*")
                flash("Confirmado")
                return render_template("teacher/create_section.html", name = user.name, activated = False)
            except werkzeug.exceptions.BadRequestKeyError:
                try:
                    # si se ha creado la seccion de forma directa:
                    content_file = request.files['content_file']
                    task_file = request.files['task_file']
                    section_name = request.form.get('name')
                    task_name = request.form.get('task_name')
                    request.form["directly"]
                    if content_file and task_file and section_name and task_name:
                        if not ('.' in task_file.filename and (task_file.filename.rsplit('.',1)[1].lower() in {'.ipynb'})):
                            flash("La extension de la tarea debe de ser .ipynb")
                            return render_template("teacher/create_section.html", name = user.name, activated = False)
                        section = Section(course_id = course.id, name = section_name, content_name = content_file.filename, task_name = task_name)
                        unreleased = UnreleasedSection(teacher_id = user.id, course_id = course.id, name = section_name, content_name = content_file.filename, task_name = task_name)
                        try:
                            db.session.add(section)
                            db.session.add(unreleased)
                            db.session.commit()
                        except Exception:
                            db.session.rollback()
                            flash("No permitido: Algún dato ya pertenece a otra sección")
                            return render_template("teacher/create_section.html",  user = user, activated = False)

                        db.session.delete(unreleased)
                        db.session.commit()
                        content_path = "courses/" + course.name + "/content"
                        source_path = "courses/" + course.name + "/source/" + task_name
                        os.mkdir(os.path.join(os.path.abspath(os.path.dirname(__file__)), source_path))
                        content_file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),content_path ,content_file.filename))
                        task_file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),source_path ,task_name + ".ipynb"))
                        manager = NbgraderManager(course.name)
                        manager.create_assigment(task_name)
                        manager.closeDB()
                        flash("Sección creada con exito")
                        return redirect(url_for('teacher_courses_course', course = course.name))
                    else:
                        flash("Rellene todos los campos necesarios para realizar esta acción")
                        return render_template("teacher/create_section.html",  user = user, activated = False)
                except werkzeug.exceptions.BadRequestKeyError:
                    # si se crea de forma manual activando el kernel
                    if content_file and section_name and task_name:
                        section = Section(course_id = course.id, name = section_name, content_name = content_file.filename, task_name = task_name)
                        unreleased = UnreleasedSection(teacher_id = user.id, course_id = course.id, name = section_name, content_name = content_file.filename, task_name = task_name)
                        try:
                            db.session.add(section)
                            db.session.add(unreleased)
                            db.session.commit()
                        except Exception:
                            db.session.rollback()
                            flash("No permitido: Algún dato ya pertenece a otra sección")
                            return render_template("teacher/create_section.html",  user = user, activated = False)
                        db.session.delete(section)
                        db.session.commit()
                        content_path = "courses/" + course.name + "/content"
                        source_path = "courses/" + course.name + "/source/" + task_name
                        os.mkdir(os.path.join(os.path.abspath(os.path.dirname(__file__)), source_path))
                        content_file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),content_path ,content_file.filename))

                        source_path = source_path + "/"
                        destiny = os.path.join(os.path.abspath(os.path.dirname(__file__)), source_path)
                        base_notebook_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "courses/" + course.name + "/base_notebook.ipynb" )
                        shutil.copy(base_notebook_path, destiny)

                        new_name = os.path.join(os.path.abspath(os.path.dirname(__file__)), source_path + task_name + ".ipynb")
                        current_name = os.path.join(os.path.abspath(os.path.dirname(__file__)), source_path +  "base_notebook.ipynb")
                        os.rename(current_name, new_name)

                        os.system("pkill -f -1 jupyter*")
                        os.system("jupyter notebook --ip='0.0.0.0' --no-browser --allow-root --port=8888 &")
                    else:
                        flash("Rellene todos los campos necesarios para realizar esta acción")
                        return render_template("teacher/create_section.html",  user = user, activated = False)
                    return render_template("teacher/create_section.html",  user = user, activated = True)
            
        else:
            return render_template("teacher/create_section.html",  user = user, activated = False)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))


@app.route('/teacher/califications',methods=["GET"])
@login_required
def teacher_califications():
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        califications = get_teachers_califications(user.id)
        return render_template("teacher/califications.html",  user = user, califications = califications)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))

@app.route('/teacher/students',methods=["GET"])
@login_required
def teacher_students():
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        enrrolled = get_teacher_students(user.id)
        return render_template("teacher/students.html",  user = user, enrrolled = enrrolled)
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
        return render_template("teacher/create_student.html",  user = user, form = form, courses = courses)
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
        return render_template("teacher/student.html", user = user, student = student.username, califications = califications)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))



@app.route('/student',methods=["GET"])
@login_required
def student():
    if check_access("student"):
        user = get_current_User(current_user.get_id())
        return render_template("student.html",  user = user)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('teacher'))


@app.route('/student/courses',methods=["GET"])
@login_required
def student_courses():
    if check_access("student"):
        user = get_current_User(current_user.get_id())
        return render_template("student/courses.html",  user = user, courses = get_student_courses(user.id))
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
                        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),path ,file.filename))
                        manager = NbgraderManager(course)
                        score = manager.grade(task,user.username)
                        calification = Calification(student_id = user.id, section_id = section, task_name = task, value = score)
                        db.session.add(calification)
                        db.session.commit()
                        manager.closeDB()
                    
        current_course = Course.query.filter_by(name = course).first()
        sections = get_sections_data(current_course.id, user.id)
        return render_template("student/course.html", course = course,  user = user, sections = sections)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('teacher'))



@app.route('/download_content/<string:course>/<string:filename>')
@login_required
def download_content(course,filename):
    path = "courses/" + course + "/content"
    return send_from_directory(path, filename, as_attachment=True)


@app.route('/download_task/<string:course>/<string:filename>')
@login_required
def download_task(course,filename):
    path = "courses/" + course + "/release/" + filename
    notebook = filename + ".ipynb"
    return send_from_directory(path, notebook, as_attachment=True)


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
        return render_template("student/course_califications.html", course = course,  user = user, califications = califications)
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
        return render_template("student/califications.html", user = user, califications = califications)
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
