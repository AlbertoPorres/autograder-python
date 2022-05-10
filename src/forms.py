from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=32)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('RememberMe')
    submit = SubmitField('Login')

