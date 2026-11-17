from flask import Blueprint, request

from models.questions import *
from models.possible_answers import *
from models.participation import *

import sqlite3
from contextlib import closing
from pathlib import Path

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
    def get_quiz_info():
        return {
            "size": repository.count(),
            "scores": participation_repository.get_scores(),
        }, 200

    @app.route('/questions/<int:question_id>', methods=['GET'])
    def get_quiz_by_id(question_id):
        question = repository.get_byid(question_id)

        if question is None:
            return {"error": "Question introuvable"}, 404

        return question, 200

    @app.route('/questions', methods=['GET'])
    def get_quiz_by_position():
        position = request.args.get("position", type=int)

        if position is None or position < 1:
            return {"error": "Une position entière positive est attendue"}, 400

        question = repository.get_by_position(position)

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
    @jwt_service.required
    def post_question():
        data = request.get_json(silent=True)


        if not isinstance(data, dict):
            return {"error": "Un objet JSON est attendu"}, 400
        try:
            question = question_from_json(data)
        except KeyError as exc:
            return {"error": f"Champ manquant : {exc.args[0]}"}, 400

        question_id = repository.insert(question)

        for answer_data in data["possibleAnswers"]:
            answer = possible_answer_from_json(answer_data,question_id=question_id,)
            answer_repository.insert(question_id, answer)


        response = question_to_json(question)
        response["id"] = question_id
        return response, 200


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

    @app.route("/participations", methods=["POST"])
    def post_participation():
        data = request.get_json(silent=True)

        if (
            not isinstance(data, dict)
            or not isinstance(data.get("playerName"), str)
            or not isinstance(data.get("answers"), list)
        ):
            return {"error": "playerName et answers sont obligatoires"}, 400

        try:
            score = participation_repository.calculate_score(data["answers"])
        except ValueError as error:
            return {"error": str(error)}, 400

        participation = Participation(data["playerName"], score)
        participation_repository.insert(participation)

        return {"playerName": data["playerName"], "score": score}, 200


    @app.route("/rebuild-db", methods=["POST"])
    @jwt_service.required
    def rebuild_db():
        sql = Path(__file__).with_name("database.sql").read_text(
            encoding="utf-8"
        )

        with closing(sqlite3.connect(repository.path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.executescript(sql)

        return "Ok", 200
    
    ### PUT 

    @app.route("/questions/<int:question_id>", methods=["PUT"])
    @jwt_service.required
    def update_question(question_id):
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return {"error": "Un objet JSON est attendu"}, 400

        try:
            question = question_from_json(data)
            answers = [
                possible_answer_from_json(item, question_id)
                for item in data["possibleAnswers"]
            ]
        except KeyError as exc:
            return {"error": f"Champ manquant : {exc.args[0]}"}, 400

        updated = repository.update(question_id, question, answers)

        if not updated:
            return {"error": "Question introuvable"}, 404

        return "", 204

    ### DELETE

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    @jwt_service.required
    def delete_question(question_id):
        deleted = repository.delete(question_id)

        if not deleted:
            return {"error": "Question introuvable"}, 404

        return "", 204


    @app.route("/questions/all", methods=["DELETE"])
    @jwt_service.required
    def delete_all_questions():
        repository.delete_all()
        return "", 204


    @app.route("/participations/all", methods=["DELETE"])
    @jwt_service.required
    def delete_all_participants():
        participation_repository.delete_all()
        return "", 204

    
    return app