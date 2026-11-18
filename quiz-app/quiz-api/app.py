from flask import Flask
from flask_cors import CORS
from flask import request

import os
from dotenv import load_dotenv

from hash import HashGen, HashCompare
from jwt_utils import JWToken

from pathlib import Path

from models.questions import QuestionRepository
from models.possible_answers import PossibleAnswerRepository
from models.participation import ParticipationRepository
from routes import create_routes

from flasgger import Swagger

load_dotenv()

app = Flask(__name__)
CORS(app)

if os.getenv("APP_ENV", "prod").lower() == "dev":
    from flasgger import Swagger

    Swagger(app, template_file="swagger.yml")
    
jwt_service = JWToken()

database_path = Path(__file__).with_name("database")

repository = QuestionRepository(database_path)
answer_repository = PossibleAnswerRepository(database_path)
participation_repository = ParticipationRepository(database_path)

app.register_blueprint(
    create_routes(
        repository,
        answer_repository,
        participation_repository,
        jwt_service,
    )
)

if __name__ == "__main__":
    app.run()
