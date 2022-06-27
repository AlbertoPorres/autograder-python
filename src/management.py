""" management class module.

    Nbgrader API and DB management class module.

    Author: Alberto Porres Fernández
    Date: 07/07/2022
"""


from nbgrader.apps import NbGraderAPI
from nbgrader.api import Gradebook
from traitlets.config import Config


# PRUEBA DE MANEJO DE LA API Y BASE DE DATOS DE NBGRADER 
class NbgraderManager:
    """ Class responsible of handling the Nbgrader API and DB conexion usage.
    """

    def __init__(self, course_name):
        """ Initialization/constructor method.

        Parameters:
            - course_name: (string) courses name

        """

        root_chain = "src/courses/" + course_name
        db_chain = "sqlite:///src/courses/"+ course_name + "/gradebook.db"
    
        config = Config()
        config.CourseDirectory.root = root_chain
        config.CourseDirectory.course_id = course_name
    
        self.api = NbGraderAPI(config = config)
        self.dbConnection = Gradebook(db_chain, course_name)


    def add_student(self, student):
        """ Adds a student to the Nbgrader database.

        Parameters:
            - student: (string) student's username
            
        """
        self.dbConnection.add_student(student)

    
    def remove_student(self, student):
        """ Removes a student from the Nbgrader database.

        Parameters:
            - student: (string) student's username
            
        """
        self.dbConnection.remove_student(student)


    def grade(self, task, student):
        """ Removes a student from the Nbgrader database.

        Parameters:
            - task: (string) tasks's name
            - student: (string) student's username
        
        Returns:
            - False if the operation did not succeed
            - The calification the student recieved

        """

        result = self.api.autograde(task,student)
        if not result["success"]:
            return False
        submision = self.dbConnection.find_submission(task,student)
        # nota sobre 10
        grade = submision.score * 10 / submision.max_score
        return round(grade,2)


    def is_submitted(self, task, student):
        """ Checks if a task has been submitted by a student or not.

        Parameters:
            - task: (string) tasks's name
            - student: (string) student's username
        
        Returns:
            - True 
            - False 

        """
        try:
            self.dbConnection.find_submission(task,student)
        except:
            return False
        else:
            return True

    def remove_submission(self, task, student):
        """ Removes a submission from the Nbgrader database.

        Parameters:
            - task: (string) tasks's name
            - student: (string) student's username 

        """
        if self.is_submitted(task,student):
            self.dbConnection.remove_submission(task,student)
        

    def create_assigment(self, task):
        """ Checks if a task has been submitted by a student or not.

        Parameters:
            - task: (string) tasks's name
            - student: (string) student's username
        
        Returns:
            - True 
            - False 

        """
        result = self.api.generate_assignment(task)
        if not result["success"]:
            return False
        else:
            return True


    def generate_feedback(self,task, student):
        """ Generates student's submission feedback file.

        Parameters:
            - task: (string) tasks's name
            - student: (string) student's username

        """
        self.api.generate_feedback(task,student)

    def remove_assigment(self,task):
        """ Removes an assigment from the DB.

        Parameters:
            - task: (string) tasks's name
        """
        self.dbConnection.remove_assignment(task))


    def closeDB(self):
        """ Closes the database connection.

        """
        self.dbConnection.close()
