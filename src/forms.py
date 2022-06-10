from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(max=32)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Login')


class ChagePasswordForm(FlaskForm):
    current_password = PasswordField('Contraseña actual', validators=[DataRequired()])
    new_password_1 = PasswordField('Nueva contraseña', validators=[DataRequired()])
    new_password_2 = PasswordField('Repita la nueva contraseña', validators=[DataRequired()])
    submit = SubmitField('Cambiar contraseña')


class CreateStudentForm(FlaskForm):
    name = StringField('Nombre del alumno', validators=[DataRequired(), Length(max=32)])
    username = StringField('Nombre de usuario del alumno', validators=[DataRequired(), Length(max=32)])
    password = PasswordField('Contraseña temporal', validators=[DataRequired()])
    confirm_password = PasswordField('Repita la contraseña', validators=[DataRequired()])


class CreateCourseForm(FlaskForm):
    name = StringField('Nombre del curso', validators=[DataRequired(), Length(max=32)])
    description = StringField('Descripcion del curso', validators=[DataRequired(), Length(max=700)])
