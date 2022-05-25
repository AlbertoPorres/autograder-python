from flask import render_template, request, redirect, url_for, flash
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from src.forms import LoginForm
import webbrowser
import os
from src.models import User
from src import app, db


#Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


db.drop_all()
db.create_all()

# manually added users
Teacher = User(username = "Teacher1", password = "1234", is_teacher = True)
Student = User(username = "Student1", password = "1234")
db.session.add(Teacher)
db.session.add(Student)
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
    return render_template("teacher/teacher.html")

@app.route('/student',methods=["GET", "POST"])
@login_required
def student():
    if request.method == 'POST':
        return None
    return render_template("student/student.html")