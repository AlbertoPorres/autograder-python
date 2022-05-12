from flask_login import UserMixin
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_teacher = db.Column(db.Boolean, default=False)




# no hay db aun
# users = []
# user1 = User(1,"Teacher1", "1234", True)
# user2 = User(1,"Student1", "1234")
# users.append(user1)
# users.append(user2)

