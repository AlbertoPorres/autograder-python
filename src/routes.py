""" routes class module.

    Web endpoints hanndler class module.

    Author: Alberto Porres Fernández
    Date: 07/07/2022
"""


from flask import render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from src.forms import LoginForm, ChagePasswordForm, CreateStudentForm, CreateCourseForm
from src.management import NbgraderManager
from src.models import User, Course, Section, Calification, CourseMembers, UnreleasedSection
from src import app, db
import os
import shutil


# KEEP JUPYTER NOTEBOOK RUNNING
# kill any jupyter current instance
os.system("pkill -f -1 jupyter*")
# run jupyter
os.system("jupyter notebook --ip='0.0.0.0' --no-browser --allow-root --port=8888 --notebook-dir=src/courses &")

#Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    """ Loads the current user getter for the login manager.

        Parameters:
            - user_id: (int) user's id 
    """
    return User.query.get(int(user_id))

# ROUTES
@app.route('/',methods=["GET"])
def index():
    """ Website's langing enpoint.            
    """
    return render_template("index.html")

@app.route('/login',methods=["GET", "POST"])
def login():
    """ Website's login enpoint.            
    """
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

    return render_template("login.html", form = form)

@app.route('/logout',methods=["GET", "POST"])
@login_required
def logout():
    """ Website's logout enpoint.            
    """
    user = get_current_User(current_user.get_id())
    logout_user()
    return redirect(url_for('login'))



@app.route('/change_password',methods=["GET", "POST"])
@login_required
def change_password():
    """ Website's password changing enpoint.            
    """
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

@app.route('/teacher',methods=["GET"])
@login_required
def teacher():
    """ Teacher's main page enpoint.            
    """
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        return render_template("teacher.html", user = user)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))

@app.route('/teacher/courses',methods=["GET"])
@login_required
def teacher_courses():
    """ Teacher's courses page enpoint.            
    """
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
    """ Teacher's individual course page enpoint.   

        Parameters:
            - course: (string) course's name          
    """
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
    """ Teacher's course students page enpoint.  

        Parameters:
            - course: (string) course's name             
    """
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


@app.route('/teacher/delete_submission/<string:course>/<string:student>/<string:task_name>',methods=["GET"])
@login_required
def teacher_delete_submission(course,student,task_name):
    """ Teacher's submission deletation enpoint.        
    
        Parameters:
            - course: (string) course's name   
            - student: (string) student's name 
            - task_name: (string) task's name 
    """
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        course = Course.query.filter_by(name = course).first()
        student = User.query.filter_by(username = student).first()
        section = Section.query.filter_by(task_name = task_name).first()
        calification = Calification.query.filter_by(student_id=student.id, section_id=section.id).first()
        if not calification:
            flash('Esta entrega ya habia sido eliminada')
            return redirect(url_for("teacher_students_student", student = student.username))
        manager = NbgraderManager(course.name)
        manager.remove_submission(section.task_name,student.username)
        manager.closeDB()
        path_submission= "courses/" + course.name + "/submitted/" + student.username + "/" + section.task_name + "/" + section.task_name + ".ipynb"
        path_feedback= "courses/" + course.name + "/feedback/" + student.username + "/" + section.task_name + "/" + section.task_name + ".html"
        os.remove(os.path.join(os.path.abspath(os.path.dirname(__file__)),path_submission))
        os.remove(os.path.join(os.path.abspath(os.path.dirname(__file__)),path_feedback))
        db.session.delete(calification)
        db.session.commit()
        flash('Entrega eliminada')
        return redirect(url_for("teacher_students_student", student = student.username))
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))


@app.route('/teacher/quick/<string:course>/<string:student>',methods=["GET"])
@login_required
def teacher_quick_student(course,student):
    """ Teacher's quick student from course enpoint.        
    
        Parameters:
            - course: (string) course's name   
            - student: (string) student's name 
    """
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
    """ Teacher's enrroll student in course enpoint.

        Parameters:
            - course: (string) course's name   
            - student: (string) student's name             
    """
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
        make_dir_submissions_feedback(course.name, student.username)
        flash("Alumno añadido al curso")
        return redirect(url_for("teacher_course_students",course = course.name))

    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))


@app.route('/teacher/create_course',methods=["GET", "POST"])
@login_required
def teacher_create_course():
    """ Teacher's course creation enpoint.            
    """
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



@app.route('/teacher/<string:course>/create_section',methods=["GET", "POST"])
@login_required
def teacher_create_section(course):
    """ Teacher's section creation in course enpoint.    
        
        Parameters:
            - course: (string) course's name 
    """
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        course = Course.query.filter_by(name = course).first()
        if request.method == 'POST':
            content_file = request.files['content_file']
            task_file = request.files['task_file']
            section_name = request.form.get('name')
            task_name = request.form.get('task_name')
            if content_file and task_file and section_name and task_name:
                if not ('.' in task_file.filename and task_file.filename.rsplit('.',1)[1].lower() == 'ipynb'):
                    flash( task_file.filename.rsplit('.',1)[1].lower())
                    flash("La extension de la tarea debe de ser .ipynb")
                    return render_template("teacher/create_section.html", user = user)
                section = Section(course_id = course.id, name = section_name, content_name = content_file.filename, task_name = task_name)
                unreleased = UnreleasedSection(teacher_id = user.id, course_id = course.id, name = section_name, content_name = content_file.filename, task_name = task_name)
                try:
                    db.session.add(section)
                    db.session.add(unreleased)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    flash("No permitido: Algún dato ya pertenece a otra sección")
                    return render_template("teacher/create_section.html",  user = user)

                db.session.delete(unreleased)
                db.session.commit()
                source_path = "courses/" + course.name + "/source/" + task_name
                os.mkdir(os.path.join(os.path.abspath(os.path.dirname(__file__)), source_path))
                task_file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),source_path ,task_name + ".ipynb"))
                manager = NbgraderManager(course.name)
                if not manager.create_assigment(task_name):
                    flash("Hay algún error en el archivo tarea")
                    db.session.delete(section)
                    db.session.commit()
                    shutil.rmtree(os.path.join(os.path.abspath(os.path.dirname(__file__)),source_path))
                    return render_template("teacher/create_section.html",  user = user)
                content_path = "courses/" + course.name + "/content"
                content_file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),content_path ,content_file.filename))
                manager.closeDB()
                relationships = CourseMembers.query.filter_by(course_id = course.id).all()
                for relation in relationships:
                    student = User.query.filter_by(id = relation.student_id).first()
                    submitted_path = "courses/" + course.name + "/submitted/" + student.username + "/" + section.task_name
                    feedback_path = "courses/" + course.name + "/feedback/" + student.username + "/" + section.task_name
                    os.mkdir(os.path.join(os.path.abspath(os.path.dirname(__file__)), submitted_path))
                    os.mkdir(os.path.join(os.path.abspath(os.path.dirname(__file__)), feedback_path))
                flash("Sección creada con exito")
                return redirect(url_for('teacher_courses_course', course = course.name))
            else:
                flash("Rellene todos los campos necesarios para realizar esta acción")
                return render_template("teacher/create_section.html",  user = user)
        else:
            return render_template("teacher/create_section.html",  user = user)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))


@app.route('/teacher/<string:course>/create_unreleased_section',methods=["GET", "POST"])
@login_required
def teacher_create_unreleased_section(course):
    """ Teacher's unreleased section creation in course enpoint.    
        
        Parameters:
            - course: (string) course's name 
    """
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        course = Course.query.filter_by(name = course).first()
        if request.method == 'POST':
            content_file = request.files['content_file']
            section_name = request.form.get('name')
            task_name = request.form.get('task_name')
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
                    return render_template("teacher/create_unreleased_section.html",  user = user)
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
                flash("Sección no publicada creada con exito")
                return redirect(url_for('teacher_unreleased_sections', course = course.name))
                
            else:
                flash("Rellene todos los campos necesarios para realizar esta acción")
                return render_template("teacher/create_unreleased_section.html",  user = user)
        else:
            return render_template("teacher/create_unreleased_section.html",  user = user)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))

@app.route('/teacher/<string:course>/unreleased_sections',methods=["GET"])
@login_required
def teacher_unreleased_sections(course):
    """ Teacher's unreleased sections page enpoint.    
        
        Parameters:
            - course: (string) course's name 
    """
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        course = Course.query.filter_by(name = course).first()
        return render_template("teacher/unreleased_sections.html",course = course, user = user, sections = UnreleasedSection.query.filter_by(teacher_id = user.id, course_id = course.id).all())
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))



@app.route('/publish_section/<string:course>/<string:section>',methods=["GET"])
@login_required
def publish_section(course, section):
    """ Teacher's publish unreleased sections enpoint.    
        
        Parameters:
            - course: (string) course's name 
            - section: (string) section's name 
    """
    if check_access("teacher"):
        course = Course.query.filter_by(name = course).first()
        user = get_current_User(current_user.get_id())
        unreleased = UnreleasedSection.query.filter_by(name = section).first()
        if not unreleased:
            flash("Accion no permitida")
            return render_template("teacher/unreleased_sections.html",course = course, user = user, sections = UnreleasedSection.query.filter_by(teacher_id = user.id, course_id = course.id).all())
        section = Section(course_id = unreleased.course_id, name = unreleased.name, content_name = unreleased.content_name, task_name = unreleased.task_name)
        manager = NbgraderManager(course.name)
        if not manager.create_assigment(section.task_name):
            flash("Hay algún problema en su tarea, compruebe su contenido")
            manager.closeDB()
            return render_template("teacher/unreleased_sections.html",course = course, user = user, sections = UnreleasedSection.query.filter_by(teacher_id = user.id, course_id = course.id).all())
        manager.closeDB()
        db.session.add(section)
        db.session.delete(unreleased)
        db.session.commit()
        relationships = CourseMembers.query.filter_by(course_id = course.id).all()
        for relation in relationships:
            student = User.query.filter_by(id = relation.student_id).first()
            path_submitted = os.path.join(os.path.abspath(os.path.dirname(__file__)), "courses/" + course.name + "/submitted/" + student.username + "/" + section.task_name)
            path_feedback = os.path.join(os.path.abspath(os.path.dirname(__file__)), "courses/" + course.name + "/feedback/" + student.username + "/" + section.task_name)
            os.mkdir(path_submitted)
            os.mkdir(path_feedback)
        return render_template("teacher/unreleased_sections.html",course = course, user = user, sections = UnreleasedSection.query.filter_by(teacher_id = user.id, course_id = course.id).all())
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))

@app.route('/cancel_section/<string:course>/<string:section>',methods=["GET"])
@login_required
def cancel_section(course, section):
    """ Teacher's cancel unreleased sections enpoint.    
        
        Parameters:
            - course: (string) course's name 
            - section: (string) section's name 
    """
    if check_access("teacher"):
        course = Course.query.filter_by(name = course).first()
        user = get_current_User(current_user.get_id())
        unreleased = UnreleasedSection.query.filter_by(name = section).first()
        if not unreleased:
            flash("Accion no permitida")
            return render_template("teacher/unreleased_sections.html",course = course, user = user, sections = UnreleasedSection.query.filter_by(teacher_id = user.id, course_id = course.id).all())
        path_content = "courses/" + course.name + "/content/" + unreleased.content_name
        path_task = "courses/" + course.name + "/source/" + unreleased.task_name
        os.remove(os.path.join(os.path.abspath(os.path.dirname(__file__)),path_content))
        shutil.rmtree(os.path.join(os.path.abspath(os.path.dirname(__file__)),path_task))
        db.session.delete(unreleased)
        db.session.commit()
        return render_template("teacher/unreleased_sections.html",course = course, user = user, sections = UnreleasedSection.query.filter_by(teacher_id = user.id, course_id = course.id).all())
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))


@app.route('/delete_course/<string:course_name>',methods=["GET"])
@login_required
def delete_course(course_name):
    """ Teacher's course deletation enpoint.    
        
        Parameters:
            - course_name: (string) course's name 
    """
    if check_access("teacher"):
        course = Course.query.filter_by(name = course_name).first()
        user = get_current_User(current_user.get_id())
        if not course:
            courses = Course.query.filter_by(teacher_id = user.id).all()
            flash("Acción no permitida")
            return render_template("teacher/courses.html",  user = user, courses = courses)
        course_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "courses/" + course.name)
        shutil.rmtree(course_path)
        sections = get_course_sections(course)
        for section in sections:
            califications = Calification.query.filter_by(section_id = section.id).all()
            for calification in califications:
                db.session.delete(calification)
            db.session.delete(section)
        unreleased_sections = UnreleasedSection.query.filter_by(course_id = course.id).all()
        for unreleased in unreleased_sections:
            db.session.delete(unreleased)
        relationships = CourseMembers.query.filter_by(course_id = course.id).all()
        for relation in relationships:
            db.session.delete(relation)
        db.session.delete(course)
        db.session.commit()
        flash("Curso borrado con exito")
        return render_template("teacher/courses.html",  user = user, courses = Course.query.filter_by(teacher_id = user.id).all())
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))




@app.route('/delete_section/<string:course_name>/<string:section_name>',methods=["GET"])
@login_required
def delete_section(course_name,section_name):
    """ Teacher's section deletation from course enpoint.    
        
        Parameters:
            - course_name: (string) course's name 
            - section_name: (string) section's name
    """
    if check_access("teacher"):
        section = Section.query.filter_by(name = section_name).first()
        course = Course.query.filter_by(name = course_name).first()
        user = get_current_User(current_user.get_id())
        if not section:
            sections = Section.query.filter_by(course_id = course.id).all()
            flash("Acción no permitida")
            return render_template("teacher/course.html",  user = user, sections = sections, course = course)

        califications = Calification.query.filter_by(section_id = section.id).all()
        for calification in califications:
            db.session.delete(calification)  
        
        manager = NbgraderManager(course.name)
        relationships = CourseMembers.query.filter_by(course_id = course.id).all()
        for relation in relationships:
            student = User.query.filter_by(id = relation.student_id).first()
            path_submitted = os.path.join(os.path.abspath(os.path.dirname(__file__)), "courses/" + course.name + "/submitted/" + student.username + "/" + section.task_name)
            path_feedback = os.path.join(os.path.abspath(os.path.dirname(__file__)), "courses/" + course.name + "/feedback/" + student.username + "/" + section.task_name)
            shutil.rmtree(path_submitted)
            shutil.rmtree(path_feedback)
            manager.remove_submission(section.task_name, student.username)

        manager.remove_assigment(section.task_name)
        content_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "courses/" + course.name + "/content/" + section.content_name)
        os.remove(content_path)
        source_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "courses/" + course.name + "/source/" + section.task_name)
        shutil.rmtree(source_path)
        release_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "courses/" + course.name + "/release/" + section.task_name)
        shutil.rmtree(release_path)
        db.session.delete(section)  
        db.session.commit()
        flash("Sección borrada con exito")
        return render_template("teacher/course.html",  user = user, sections = Section.query.filter_by(course_id = course.id).all(), course = course)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))

@app.route('/teacher/califications',methods=["GET"])
@login_required
def teacher_califications():
    """ Teacher's califications page enpoint. 
    """    
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
    """ Teacher's students page enpoint. 
    """  
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
    """ Teacher's student delatation page enpoint. 

        Parameters:
            - student_id: (int) student's id
    """  
    if check_access("teacher"):
        student = User.query.filter_by(id = student_id).first()
        courses = get_student_courses(student_id)
        relationships = CourseMembers.query.filter_by(student_id = student_id).all()
        califications = Calification.query.filter_by(student_id = student_id).all()
        for course in courses:
            path_submitted = os.path.join(os.path.abspath(os.path.dirname(__file__)), "courses/" + course.name + "/submitted/" + student.username)
            path_feedback = os.path.join(os.path.abspath(os.path.dirname(__file__)), "courses/" + course.name + "/feedback/" + student.username)
            shutil.rmtree(path_submitted)
            shutil.rmtree(path_feedback)
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
    """ Teacher's student creation page enpoint. 
    """  
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
                        make_dir_submissions_feedback(course.name, user.username)
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
    """ Teacher's single student page enpoint. 

        Parameters:
            - student: (string) student's name
    """  
    if check_access("teacher"):
        user = get_current_User(current_user.get_id())
        student = User.query.filter_by(username = student).first()
        if not student:
            return redirect(url_for("teacher_students"))
        if request.method == 'POST':
            return redirect(url_for('delete_student', student_id = student.id))
        courses = get_student_courses(student.id)
        califications = get_student_califications(student, courses, user)
        return render_template("teacher/student.html", user = user, student = student, califications = califications)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('student'))



@app.route('/student',methods=["GET"])
@login_required
def student():
    """ Student's main page enpoint.            
    """
    if check_access("student"):
        user = get_current_User(current_user.get_id())
        return render_template("student.html",  user = user)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('teacher'))


@app.route('/student/courses',methods=["GET"])
@login_required
def student_courses():
    """ Student's courses page enpoint.            
    """
    if check_access("student"):
        user = get_current_User(current_user.get_id())
        return render_template("student/courses.html",  user = user, courses = get_student_courses(user.id))
    else:
        flash("Acceso no permitido")
        return redirect(url_for('teacher'))



@app.route('/student/courses/<string:course>',methods=["GET", "POST"])
@login_required
def student_course(course):
    """ Student's course content page enpoint.    

        Parameters:
            - course: (string) course's name
    """
    if check_access("student"):
        user = get_current_User(current_user.get_id())
        current_course = Course.query.filter_by(name = course).first()
        sections = get_sections_data(current_course.id, user.id)
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
                        path = "courses/" + course + "/submitted/" + user.username + "/" + task 
                        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),path ,file.filename))
                        manager = NbgraderManager(course)
                        score = manager.grade(task,user.username)
                        if not score:
                            flash("Hay algo erroneo en su archivo de entrega")
                            os.remove(os.path.join(os.path.abspath(os.path.dirname(__file__)),path + "/" + file.filename))
                            return render_template("student/course.html", course = current_course,  user = user, sections = sections)
                        calification = Calification(student_id = user.id, section_id = section, task_name = task, value = score)
                        db.session.add(calification)
                        db.session.commit()
                        manager.generate_feedback(task,user.username)
                        manager.closeDB()
                        path = os.path.join(os.path.abspath(os.path.dirname(__file__)),  "courses/" + course + "/autograded/" + user.username)
                        shutil.rmtree(path)
                        flash("Su tarea ha sido enviada")
                        return render_template("student/course.html", course = current_course,  user = user, sections = get_sections_data(current_course.id, user.id))
        return render_template("student/course.html", course = current_course,  user = user, sections = sections)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('teacher'))


@app.route('/student/course/<string:course>/<string:username>',methods=["GET"])
@login_required
def student_course_califications(course, username):
    """ Student's course califications page enpoint.    

        Parameters:
            - course: (string) course's name
            - username: (string) student's username
    """
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
        return render_template("student/course_califications.html", course = current_course,  user = user, califications = califications)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('teacher'))

@app.route('/student/califications',methods=["GET"])
@login_required
def student_califications():
    """ Student's califications page enpoint.
    """
    if check_access("student"):
        user = get_current_User(current_user.get_id())
        courses = get_student_courses(user.id)
        califications = get_student_califications_(user, courses)
        return render_template("student/califications.html", user = user, califications = califications)
    else:
        flash("Acceso no permitido")
        return redirect(url_for('teacher'))


@app.route('/download_content/<string:course>/<string:filename>')
@login_required
def download_content(course,filename):
    """ Course section content downloader endpoint.

        Parameters:
            - course: (string) course's name
            - filename: (string) file name
    """
    path = "courses/" + course + "/content"
    return send_from_directory(path, filename, as_attachment=True)


@app.route('/download_task/<string:course>/<string:filename>')
@login_required
def download_task(course,filename):
    """ Course section task downloader endpoint.

        Parameters:
            - course: (string) course's name
            - filename: (string) file name
    """
    path = "courses/" + course + "/release/" + filename
    notebook = filename + ".ipynb"
    return send_from_directory(path, notebook, as_attachment=True)


@app.route('/download_source/<string:course>/<string:filename>')
@login_required
def download_source(course,filename):
    """ Course task source version downloader endpoint.

        Parameters:
            - course: (string) course's name
            - filename: (string) file name
    """
    path = "courses/" + course + "/source/" + filename
    notebook = filename + ".ipynb"
    return send_from_directory(path, notebook, as_attachment=True)


@app.route('/download_submission/<string:course>/<string:student>/<string:task_name>')
@login_required
def download_submission(course, student, task_name):
    """ Course submission downloader endpoint.

        Parameters:
            - course: (string) course's name
            - student: (string) student's name
            - task_name: (string) task bame
    """
    path = "courses/" + course + "/submitted/" + student + "/" + task_name
    notebook = task_name + ".ipynb"
    return send_from_directory(path, notebook, as_attachment=True)


@app.route('/download_feedback/<string:course>/<string:student>/<string:task_name>')
@login_required
def download_feedback(course, student, task_name):
    """ Course feedback downloader endpoint.

        Parameters:
            - course: (string) course's name
            - student: (string) student's name
            - task_name: (string) task bame
    """
    path = "courses/" + course + "/feedback/" + student + "/" + task_name
    feedback_file = task_name + ".html"
    return send_from_directory(path, feedback_file, as_attachment=True)



# Aditional methods

def get_current_User(id):
    """ Session's current user getter.

        Parameters:
            - id: (int) user's id
    """
    return User.query.filter_by(id=id).first() 


def get_student_courses(student_id):
    """ Gets all the courses a student is enrrolled in.

        Parameters:
            - student_id: (int) student's id
    """
    courses = []
    relationships = CourseMembers.query.filter_by(student_id = student_id).all()
    for relationship in relationships:
        courses.append(Course.query.filter_by(id = relationship.course_id).first())
    return courses

def get_teacher_courses(teacher_id):
    """ Gets all the teacher's courses.

        Parameters:
            - teacher_id: (int) teacher's id
    """
    return Course.query.filter_by(teacher_id = teacher_id).all()

def get_course_sections(course):
    """ Gets the course's sections.

        Parameters:
            - course: (Course) course itself
    """
    sections = []
    sections_ = Section.query.filter_by(course_id = course.id).all()
    for section in sections_:
        sections.append(section)
    return sections

# for student
def get_student_califications_(user, courses):
    """ Gets all student's califications for the student.

        Parameters:
            - user: (User) the user/student itself
            - courses: (List) list of all the student's courses
    """
    califications = []
    for course in courses:
            sections = Section.query.filter_by(course_id = course.id).all()
            for section in sections:
                calification = Calification.query.filter_by(student_id=user.id, section_id=section.id).first()
                if calification:
                    tmp_list = [course.name, section.name,calification]
                    califications.append(tmp_list)
    return califications

# for teacher
def get_student_califications(user, courses, teacher):
    """ Gets student's califications in the teacher's courses for the teacher.

        Parameters:
            - user: (User) the user/student itself
            - courses: (List) list of all the student's courses
            - teacher: (User) the teacher requesting the student's califications
    """
    califications = []
    for course in courses:
        if course.teacher_id == teacher.id:
            sections = Section.query.filter_by(course_id = course.id).all()
            for section in sections:
                calification = Calification.query.filter_by(student_id=user.id, section_id=section.id).first()
                if calification:
                    tmp_list = [course.name, section.name,calification]
                    califications.append(tmp_list)
    return califications



def get_sections_data(course_id, student_id):
    """ Gets sections information for the student view of a course.

        Parameters:
            - course_id: (int) course's id
            - student_id: (int) student's id
    """
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
    """Checks the access for a student or teacher.

        Parameters:
            - user_type: (string) user type.
    """
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
    """Gets the students enrrolled in the teacher's courses.

        Parameters:
            - teacher_id: (int) teacher's id.
    """
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


def make_dir_submissions_feedback(course, username):
    """Makes de submissions and feedbacks files for a student in a course.

        Parameters:
            - course: (string) course name.
            - username: (string) student username.
    """
    path_submitted = os.path.join(os.path.abspath(os.path.dirname(__file__)), "courses/" + course + "/submitted/" + username)
    path_feedback = os.path.join(os.path.abspath(os.path.dirname(__file__)), "courses/" + course + "/feedback/" + username)
    os.mkdir(path_submitted)
    os.mkdir(path_feedback)
    course_ = Course.query.filter_by(name = course).first()
    sections = Section.query.filter_by(course_id = course_.id).all()
    for section in sections:
        s_path = path_submitted + "/" + section.task_name
        f_path = path_feedback + "/" + section.task_name
        os.mkdir(s_path)
        os.mkdir(f_path)



def get_teachers_califications(teacher_id):
    """Gets the califications for all the students enrrolled in the teacher's courses.

        Parameters:
            - teacher_id: (int) teacher's id.
    """
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
    """Removes directories for a student removal from a course.

        Parameters:
            - course: (string) course name.
            - username: (string) student username.
    """
    path_submitted = os.path.join(os.path.abspath(os.path.dirname(__file__)), "courses/" + course.name + "/submitted/" + student.username)
    path_feedback = os.path.join(os.path.abspath(os.path.dirname(__file__)), "courses/" + course.name + "/feedback/" + student.username)
    shutil.rmtree(path_submitted)
    shutil.rmtree(path_feedback)
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


        