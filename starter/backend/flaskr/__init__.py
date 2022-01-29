import json
import os
from flask import Flask, request, abort, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category


def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  #-----------------------------------#
  #---------- CORS Settings ----------#
  #-----------------------------------#

  CORS(app, resources={"/":{"origins":"*"}})



  @app.after_request
  def after_request(response):
    '''
    Access Control Settings: It sets access control headers and methods.
    '''
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
    return response
    

  @app.route('/categories')
  def get_categories():
    '''
    This endpoint returns all available categories from db
    '''
    categories = Category.query.all()

    if (len(categories)==0):
      abort(404)
    else:
      return jsonify({
        "success":True,
        "categories":{category.id:category.type for category in categories}
      }),200


  @app.route('/questions')
  def get_questions():
    '''
    This endpoint handles GET requests for questions. It retrieves questions
    per page. Up to query_string called "page", it return 10 questions, success,
    total number of available questions, and available categories. 
    '''
    page = request.args.get('page', 1, type=int)
    current_questions = Question.query.order_by(Question.id).paginate(page,10).items
    categories = Category.query.all()
    if len(current_questions)==0:
      abort(404)
    else:
      return jsonify({
        "success":True,
        "questions": [question.format() for question in current_questions],
        "total_questions": len(Question.query.all()),
        "current_category":None,
        "categories":{category.id:category.type for category in categories}

      })
    

  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    '''This endpoint handles DELETE requests for given question IDs. It takes 
    question ID as argument, then queries db based on it. Then delete target question.
    If it can not do the task, it throws a 422 error. 
    '''
    try:
      question = Question.query.get(question_id)

      if question is None:
        abort(404)

      question.delete()

      return jsonify({
        "success":True,
        "deleted": question_id
      })
    except:
      abort(422)

    
  @app.route('/questions', methods=['POST'])
  def create_question():    
    '''
    This endpoint handles with POST request that aims at creating new questions.
    It takes necessary data from related structure by using flask request and then 
    create new question using these data. Finally it inserts the question into db, or
    throws an error if necessary.
    '''
    data = request.get_json()
    question_body = data['question']
    question_answer = data['answer']
    question_category = data['category']
    question_difficulty = data['difficulty']

    if(question_body is None or question_answer is None or question_category is None or question_difficulty is None):
      abort(422)
    
    try:
      new_question = Question(question=question_body, answer=question_answer, category=question_category, difficulty=question_difficulty)
      new_question.insert()

      return jsonify({
        "success": True,
        "created": new_question.id,
        "message": "The question has been successfully created!"
      }),201
    except:
      abort(422)

  
  @app.route('/questions/search', methods=['POST'])
  def question_search():    
    '''
    This endpoint handles with searching questions based on a search term coming
    from client. It takes it and uses it to process a query into db. Then, returns
    questions that have search term as substring in their bodies.
    '''
    data = request.get_json()
    search_term = data.get("searchTerm", None)

    if search_term:
      questions = Question.query.filter(Question.question.ilike(f"%{search_term}%")).all()

      return jsonify({
        "success": True,
        "questions": [question.format() for question in questions],
        "totalQuestions": len(questions),
        "current_category":None
      })
    else:
      abort(404)


  @app.route('/categories/<int:category_id>/questions')
  def get_questions_by_category(category_id):
    '''
    This endpoint gets category id and queries db based on it. Then, it returns 
    all questions related this category. If category does not exist, it throws 404
    '''
    category = Category.query.filter_by(id=category_id).one_or_none()

    if category is None:
      abort(404)
  
    questions = Question.query.filter_by(
              category = category_id).all()

    return jsonify({
      'success': True,
      'questions': [question.format() for question in questions],
      'total_questions': len(questions),
      'current_category': category.type
    })


  @app.route('/quizzes', methods=['POST'])
  def set_quiz():
    '''
    This endpoint handles with quiz play. It takes necessary information form request 
    body (category id and previous questions). Based on that information, it sets the quiz,
    when there is no question left, it ends the quiz.
    '''
    try:
      data = request.get_json()
      category = data['quiz_category']
      prev_questions = data['previous_questions']

      if ((category is None) or (prev_questions is None)):
        abort(422)
      
      if (category['id'] == 0):
        quiz_questions = Question.query.all()
      else:
        quiz_questions = Question.query.filter_by(category=category['id']).all()
      
      next_question = quiz_questions[random.randint(0, len(quiz_questions)-1)]

      if next_question.id in prev_questions:
        next_question = quiz_questions[random.randint(0, len(quiz_questions)-1)]

      return jsonify({
          'success': True,
          'question': next_question.format(),
      }), 200

    except:
      abort(422)

  #-----------------------------------#
  #--------- Error Handlers ----------#
  #-----------------------------------#

  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success":False,
      "error":404,
      "message":"Not Found"
    }),404

  @app.errorhandler(422)
  def unprocessable_entity(error):
    return jsonify({
      "success":False,
      "error":422,
      "message":"Unprocessable Entity"
    }),422

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      "success":False,
      "error":400,
      "message":"Bad Request"
    }),400

  @app.errorhandler(405)
  def method_not_allowed(error):
    return jsonify({
      "success":False,
      "error":405,
      "message":"Method Not Allowed"
    }),405
  
  @app.errorhandler(500)
  def internal_serve_error(error):
    return jsonify({
      "success":False,
      "error":500,
      "message":"Internal Server Error"
    }),500

  return app

    