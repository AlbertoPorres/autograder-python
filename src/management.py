from distutils.command.config import config
from multiprocessing import Manager
from nbgrader.apps import NbGraderAPI
from nbgrader.api import Gradebook
from traitlets.config import Config


# PRUEBA DE MANEJO DE LA API Y BASE DE DATOS DE NBGRADER 
class NbgraderManager:

    def __init__(self, course_name):

        root_chain = "src/courses/" + course_name
        db_chain = "sqlite:///src/courses/"+ course_name + "/gradebook.db"
    
        config = Config()
        config.CourseDirectory.root = root_chain
        config.CourseDirectory.course_id = course_name
    
        self.api = NbGraderAPI(config = config)
        self.dbConnection = Gradebook(db_chain, course_name)


    def add_student(self, student):
        self.dbConnection.add_student(student)

    
    def remove_student(self, student):
        self.dbConnection.remove_student(student)


    def grade(self, task, student):
        result = self.api.autograde(task,student)
        if not result["success"]:
            return False
        submision = self.dbConnection.find_submission(task,student)
        # nota sobre 10
        grade = submision.score * 10 / submision.max_score
        return round(grade,2)


    def is_submitted(self, task, student):
        try:
            self.dbConnection.find_submission(task,student)
        except:
            return False
        else:
            return True

    def remove_submission(self, task, student):
        if self.is_submitted(task,student):
            self.dbConnection.remove_submission(task,student)
        

    def create_assigment(self, task):
        result = self.api.generate_assignment(task)
        if not result["success"]:
            return False
        else:
            return True

    def closeDB(self):
        self.dbConnection.close()
