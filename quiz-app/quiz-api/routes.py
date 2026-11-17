from flask import Blueprint, request

from questions import question_from_json, question_to_json
from hash import HashGen

def create_routes(repository, jwt_service):
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


    ### POST 
    @app.route("/login", methods=["POST"])
    def post_login():
        payload = request.get_json(silent=True)
        
        user = payload.get("user")
        password = payload.get("password")
        hashed_pass = HashGen(password)

        token = jwt_service.build({"user": user, "password": hashed_pass})

        return {"size": 0, "credentials": [user, hashed_pass], "token": token}, 200

    @app.route("/question", methods=["POST"])
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

    return app