from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, current_user, login_user
from forms import LoginForm
from models import get_user, users

app = Flask(__name__)
app.config['SECRET_KEY'] = '7110c8ae51a4b5af97be6534caef90e4bb9bdcb3380af008f90b23a5d1616bf319bc298105da20fe'
login_manager = LoginManager(app)


# prueba de manejo de form-wtf
@app.route('/',methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        #return redirect(url_for('_____'))
        return "testest"

        
    form = LoginForm()
    if form.validate_on_submit():

        user = get_user(form.username.data)
        if user is not None and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)

            username = form.username.data
            password = form.password.data
            #aqui gestionar templates siguientes
            return username + "" + password
            
        return "no deberias de haber pasado"

    return render_template("login.html", form = form)

@login_manager.user_loader
def load_user(user_id):
    for user in users:
        if user.id == int(user_id):
            return user
    return None

if __name__ =="__main__":
    app.run(host="0.0.0.0", port="5000", debug = True)

