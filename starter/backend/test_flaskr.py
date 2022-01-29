from multiprocessing.connection import answer_challenge
import os
from re import search
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia"
        self.database_path = "postgresql://{}@{}/{}".format("postgres", "localhost:5432", self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass


    def test_get_categories(self):
        '''
        Tests Categories Loading Success
        '''

        #Load Response Data
        res = self.client().get('/categories')
        data = json.loads(res.data)

        #Check status code, success, existence of categories and length of them
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['categories'])
        self.assertEqual(len(data['categories']), 6)


    def test_get_categories_404(self):
        '''
        Tests Categories Loading Failure
        '''

        #Send request with wrong category id
        res = self.client().get('/categories/123124')
        data = json.loads(res.data)

        #Check status code, success, and message
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "Not Found")


    def test_get_questions(self):
        '''
        Tests Questions Loading Success
        '''
        #Load Response Data
        res = self.client().get('/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['categories'])
        self.assertTrue(data['total_questions'])
        self.assertTrue(data['questions'])
        self.assertEqual(len(data['questions']), 10)


    def test_get_questions_404(self):
        '''
        Tests Questions Loading Failure
        '''

        #Send Request with wrong page number
        res = self.client().get('/questions?page=10')
        data = json.loads(res.data)

        #Check status code, success, and message
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "Not Found")


    def test_delete_questions(self):
        '''
            Create a mock question in order to keep db as it is after the operation
        '''
        mock_question = Question(question="This is a new question", answer="No answer", difficulty=2, category=2)
        mock_question.insert()
        mock_question_id=mock_question.id
        
        #Load Response Data
        res = self.client().delete(f'/questions/{mock_question_id}')
        data = json.loads(res.data)

        #Check status code, success, and deleted question
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['deleted'], mock_question_id)


    def test_delete_questions_422(self):
        '''
        Tests Question Delete Failure
        '''

        #Send request with wrong question id
        res = self.client().delete('/questions/10000')
        data = json.loads(res.data)

        #Check status code, success, and message
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "Unprocessable Entity")


    def test_create_question(self):
        '''
        Tests Question Create Success
        '''
        new_question = {"question":"new_question", "answer":"new answer",
                                "category":2, "difficulty":2}
        original_length = len(Question.query.all())
        res = self.client().post('/questions', json=new_question)

        new_length=len(Question.query.all())

        #Load Response Data
        data = json.loads(res.data)

        deleted_question = Question.query.filter_by(question=new_question['question']).first()
        deleted_question.delete()

        #Check status code, success, and message, length of table before and after the test
        self.assertEqual(res.status_code, 201)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['message'], "The question has been successfully created!")
        self.assertEqual(original_length+1, new_length)


    def test_create_question_422(self):
        '''
        Tests Question Create Failure
        '''
        new_question = {"question":"new question", "answer":"new answer", "difficulty":1, "category":None}
        original_length = len(Question.query.all())

        #Sends request with wrong data
        res = self.client().post('/questions', json=new_question)

        new_length=len(Question.query.all())

        #Load Response Data
        data = json.loads(res.data)

        #Check status code, success, and message, length of table before and after the test
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "Unprocessable Entity")
        self.assertEqual(original_length, new_length)


    def test_question_search(self):
        '''
        Tests Question Search Success
        '''

        #Send a valid request
        res = self.client().post('/questions/search', json={"searchTerm":"a"})
        data = json.loads(res.data)
        
        #Check status code, success, existence of questions and totalQuestions
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data['questions'])
        self.assertTrue(data['totalQuestions'])

    def test_question_search_404(self):
        '''
        Tests Question Search Failure
        '''

        #Sends a wrong request
        res = self.client().post('/questions/search', json={"searchTerm":""})
        data = json.loads(res.data)
        
        #Check status code, success, and message
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Not Found")
        

    def test_get_questions_by_category(self):
        '''
        Tests Question by Category Success
        '''

        #Get Questions by ID 1
        category_id = 1
        res = self.client().get(f'/categories/{category_id}/questions')
        data = json.loads(res.data)

        #Check status code, success, current category and existence of questions, and totalQuestions
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(len(data["questions"]))
        self.assertTrue(data["total_questions"])
        self.assertEqual(data["current_category"], "Science")


    def test_get_questions_by_category_404(self):
        '''
        Tests Question by Category Failure
        '''

        #Send request with a category id that does not exist
        category_id = 10000
        res = self.client().get(f'/category/{category_id}/questions')
        data = json.loads(res.data)

        #Check status code, success, and message
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Not Found")

    def test_set_quiz(self):
        '''
        Tests Set Quiz Succcess
        '''

        #Send a request with valid data
        res = self.client().post('/quizzes', json={
            "previous_questions":[],
            "quiz_category":{
                "id":2,
                "type":"Art"
            }
        })
        data = json.loads(res.data)

        #Check status code, success, and the existence of question
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(data["question"])
    
    
    def test__set_quiz_404(self):
        '''
        Tests Set Quiz Failure
        '''

        #Send a request with invalid data
        res = self.client().post('/quizzes', json={
            "previous_questions":[],
            "quiz_category":None
        })
        data = json.loads(res.data)

        #Check status code, success, and message
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Unprocessable Entity")
        





# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()