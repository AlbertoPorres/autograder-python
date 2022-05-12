from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from forms import LoginForm
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SECRET_KEY'] = '7110c8ae51a4b5af97be6534caef90e4bb9bdcb3380af008f90b23a5d1616bf319bc298105da20fe'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# DB model user
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique = True)
    password = db.Column(db.String(128), nullable=False)
    is_teacher = db.Column(db.Boolean, default=False)

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
    if request.method == 'POST':
        return None
    return render_template("teacher/teacher.html")

@app.route('/student',methods=["GET", "POST"])
@login_required
def student():
    if request.method == 'POST':
        return None
    return render_template("student/student.html")
    

if __name__ =="__main__":
    app.run(host="0.0.0.0", port="5000", debug = True)

