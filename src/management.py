from distutils.command.config import config
from nbgrader.apps import NbGraderAPI
from nbgrader.api import Gradebook
from traitlets.config import Config
from nbgrader.coursedir import CourseDirectory


# PRUEBA DE MANEJO DE LA API Y BASE DE DATOS DE NBGRADER 
class NbgraderManager:

    def __init__(self, course_name):

        root_chain = "courses/" + course_name
        db_chain = "sqlite:///courses/"+ course_name + "/gradebook.db"
    
        config = Config()
        config.CourseDirectory.root = root_chain
        config.CourseDirectory.course_id = course_name
    
        self.api = NbGraderAPI(config = config)
        self.dbConnection = Gradebook(db_chain, course_name)


    def autograde_test(self, task, student):
        self.api.autograde(task,student)
        submision = self.dbConnection.find_submission(task,student)
        print(submision.score)


manager = NbgraderManager("Curso de Python")
manager.autograde_test("EV_Funciones","pepe")