""" forms class module.

    WTForms forms handler class module.

    Author: Alberto Porres Fernández
    Date: 07/07/2022
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    """ Web Login form.
    """
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(max=32)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Login')


class ChagePasswordForm(FlaskForm):
    """ Web Change Password form.
    """
    current_password = PasswordField('Contraseña actual', validators=[DataRequired()])
    new_password_1 = PasswordField('Nueva contraseña', validators=[DataRequired()])
    new_password_2 = PasswordField('Repita la nueva contraseña', validators=[DataRequired()])
    submit = SubmitField('Cambiar contraseña')


class CreateStudentForm(FlaskForm):
    """ Web Create Student form.
    """
    name = StringField('Nombre del alumno', validators=[DataRequired(), Length(max=32)])
    username = StringField('Nombre de usuario del alumno', validators=[DataRequired(), Length(max=32)])
    password = PasswordField('Contraseña temporal', validators=[DataRequired()])
    confirm_password = PasswordField('Repita la contraseña', validators=[DataRequired()])


class CreateCourseForm(FlaskForm):
    """ Web Create Course form.
    """
    name = StringField('Nombre del curso', validators=[DataRequired(), Length(max=32)])
    description = StringField('Descripcion del curso', validators=[DataRequired(), Length(max=700)])

