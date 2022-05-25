from flask_login import UserMixin
from src import db
from werkzeug.security import generate_password_hash, check_password_hash



# DB model user
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique = True)
    password = db.Column(db.String(128), nullable=False)
    is_teacher = db.Column(db.Boolean, default=False)




