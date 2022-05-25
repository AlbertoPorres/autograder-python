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

    teacher_course = db.relationship('Course', backref = 'teacher')
    student_calif = db.relationship('Calification', backref = 'student')
    student_course = db.relationship('CourseMembers', backref = 'student')

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
    name = db.Column(db.String(80), nullable=False)
    content_name = db.Column(db.String(80), nullable=False)
    task_name = db.Column(db.String(80), nullable=False)

    section_calif = db.relationship('Calification', backref = 'section')

class Calification(db.Model):
    student_id = db.Column(db.Integer, db.ForeignKey('user.id') , primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), primary_key=True)
    task_name = db.Column(db.String(80), nullable=False)
    value = db.Column(db.Integer, nullable=False)


class CourseMembers(db.Model):
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)


