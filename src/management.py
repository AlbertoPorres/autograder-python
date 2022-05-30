from distutils.command.config import config
from nbgrader.apps import NbGraderAPI
from nbgrader.api import Gradebook
from traitlets.config import Config
from nbgrader.coursedir import CourseDirectory


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
        self.api.autograde(task,student)
        submision = self.dbConnection.find_submission(task,student)
        return submision.score


    def is_submitted(self, task, student):
        try:
            self.dbConnection.find_submission(task,student)
        except:
            return False
        else:
            return True

    def closeDB(self):
        self.dbConnection.close()
        


# print(manager.is_submitted("dsada","dasda"))
# print(manager.is_submitted("","dasda"))
# print(manager.is_submitted("EV_Funciones","pepe"))
# print(manager.is_submitted("EV_Funciones","pepe"))
