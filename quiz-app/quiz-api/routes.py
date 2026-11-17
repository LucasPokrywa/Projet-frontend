from flask import Blueprint, request

from models.questions import *
from models.possible_answers import *
from models.participation import *


from hash import HashGen

def create_routes(repository,answer_repository,participation_repository,jwt_service,):
    """Classe de gestion des routes de l'API
    """
    app = Blueprint("quiz", __name__)

    ### GET
    @app.route('/')
    def index():
        return "Bienvenue sur l'api quiz"

    @app.route('/quiz-info', methods=['GET'])
    def GetQuizInfo():
        return {"size": 0, "scores": []}, 200

    @app.route('/questions/<int:question_id>', methods=['GET'])
    def get_quiz_by_id(question_id):
        question = repository.get_byid(question_id)

        if question is None:
            return {"error": "Question introuvable"}, 404

        return question, 200


    ### POST 
    @app.route("/login", methods=["POST"])
    def post_login():
        payload = request.get_json(silent=True)
        
        user = payload.get("user")
        password = payload.get("password")
        hashed_pass = HashGen(password)

        token = jwt_service.build({"user": user, "password": hashed_pass})

        return {"size": 0, "credentials": [user, hashed_pass], "token": token}, 200

    @app.route("/questions", methods=["POST"])
    def post_question():
        data = request.get_json(silent=True)


        if not isinstance(data, dict):
            return {"error": "Un objet JSON est attendu"}, 400
        try:
            question = question_from_json(data)
        except KeyError as exc:
            return {"error": f"Champ manquant : {exc.args[0]}"}, 400

        question_id = repository.insert(question)

        response = question_to_json(question)
        response["id"] = question_id
        return response, 201


    @app.route("/questions/<int:question_id>/answers", methods=["POST"])
    def add_possible_answers(question_id):
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return {"error": "Un objet JSON est attendu"}, 400

        answers = data.get("possibleAnswers")

        if not isinstance(answers, list) or not answers:
            return {"error": "possibleAnswers doit être une liste non vide"}, 400

        updated_answers = repository.add_possible_answers(question_id, answers)

        if updated_answers is None:
            return {"error": "Question introuvable"}, 404

        return {"id": question_id, "possibleAnswers": updated_answers}, 200

    
    return app