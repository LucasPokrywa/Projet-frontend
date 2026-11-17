from flask import Flask
from flask_cors import CORS
from flask import request

from hash import HashGen, HashCompare
from jwt_utils import JWToken

from pathlib import Path

from questions import QuestionRepository, question_from_json, question_to_json


app = Flask(__name__)
CORS(app)
jwt_service = JWToken()

repository = QuestionRepository(Path(__file__).with_name("database"))


@app.route('/')
def hello_world():
	x = 'world'
	return f"Hello, {x}"

@app.route('/quiz-info', methods=['GET'])
def GetQuizInfo():
	return {"size": 0, "scores": []}, 200

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


if __name__ == "__main__":
    app.run()
