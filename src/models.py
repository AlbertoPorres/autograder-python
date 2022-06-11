from operator import is_
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from src import db
from werkzeug.security import generate_password_hash, check_password_hash



# DB model user
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), nullable=False, unique = True)
    password = db.Column(db.String(80), nullable=False)
    is_teacher = db.Column(db.Boolean, default=False)
    first_login = db.Column(db.Boolean, default=False)

    teacher_course = db.relationship('Course', backref = 'teacher')
    student_calif = db.relationship('Calification', backref = 'student')
    student_course = db.relationship('CourseMembers', backref = 'student')

    def __init__(self, name, username, password, is_teacher = False, first_login = False):
        self.name = name
        self.username = username
        self.password = generate_password_hash(password)
        self.is_teacher = is_teacher
        self.first_login = first_login

    def verify_password(self,pswd):
        return check_password_hash(self.password, pswd)

    def change_password(self,new_password):
        self.password = generate_password_hash(new_password)



class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(80), nullable=False, unique = True)
    description = db.Column(db.String(300), nullable=False)

    course_section = db.relationship('Section', backref = 'course')
    course_student = db.relationship('CourseMembers', backref = 'course')

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    name = db.Column(db.String(80), nullable=False,  unique = True)
    content_name = db.Column(db.String(80), nullable=False,  unique = True)
    task_name = db.Column(db.String(80), nullable=False,  unique = True)

    section_calif = db.relationship('Calification', backref = 'section')

class Calification(db.Model):
    student_id = db.Column(db.Integer, db.ForeignKey('user.id') , primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), primary_key=True)
    task_name = db.Column(db.String(80), nullable=False)
    value = db.Column(db.Integer, nullable=False)


class CourseMembers(db.Model):
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)


class UnreleasedSection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, nullable = False)
    course_id = db.Column(db.Integer, nullable = False)
    name = db.Column(db.String(80), nullable=False,  unique = True)
    content_name = db.Column(db.String(80), nullable=False,  unique = True)
    task_name = db.Column(db.String(80), nullable=False,  unique = True)

