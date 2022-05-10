from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin):

    def __init__(self, id, username, password, is_teacher=False):
        self.id = id
        self.username = username
        self.password = generate_password_hash(password)
        self.is_teacher = is_teacher

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_teacher(self):
        return self.is_teacher

# no hay db aun
users = []
user = User(1,"test", "1234")
users.append(user)

def get_user(username):
    for user in users:
        if user.username == username:
            return user
    return None