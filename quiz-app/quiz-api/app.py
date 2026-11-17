from flask import Flask
from flask_cors import CORS
from flask import request

from hash import HashGen, HashCompare
from jwt_utils import JWToken

from pathlib import Path

from questions import QuestionRepository, question_from_json, question_to_json

from routes import create_routes

app = Flask(__name__)
CORS(app)
jwt_service = JWToken()

repository = QuestionRepository(Path(__file__).with_name("database"))

app.register_blueprint(create_routes(repository, jwt_service))

if __name__ == "__main__":
    app.run()
