from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField('User Name', validators=[DataRequired(), Length(max=32)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Login')


class ChagePasswordForm(FlaskForm):
    current_password = PasswordField('Password', validators=[DataRequired()])
    new_password_1 = PasswordField('Password', validators=[DataRequired()])
    new_password_2 = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Change my password')