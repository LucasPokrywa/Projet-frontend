from flask import Blueprint, request

from models.questions import *
from models.possible_answers import *
from models.participation import *

import sqlite3
from contextlib import closing
from pathlib import Path

from hash import HashGen

import os

def create_routes(repository,answer_repository,participation_repository,jwt_service,):
    """Classe de gestion des routes de l'API
    """
    app = Blueprint("quiz", __name__)
    ADMIN_PASS = os.environ["JWT_SECRET"]

    ### GET
    @app.route('/')
    def index():
        """Afficher le message d'accueil.
        ---
        tags:
        - Accueil
        produces:
        - text/html
        responses:
          '200':
            description: Message d'accueil de l'API.
            schema:
              type: string
              example: Bienvenue sur l'api quiz
        """
        return "Bienvenue sur l'api quiz"

    @app.route('/quiz-info', methods=['GET'])
    def get_quiz_info():
        """Obtenir la taille du quiz et le classement.
        ---
        tags:
        - Quiz
        responses:
          '200':
            description: Nombre de questions et participations triées par score décroissant, puis par identifiant
              croissant en cas d'égalité.
            schema:
              type: object
              required:
              - size
              - scores
              properties:
                size:
                  type: integer
                  minimum: 0
                  example: 3
                scores:
                  type: array
                  items:
                    $ref: '#/definitions/Participation'
        """
        return {
            "size": repository.count(),
            "scores": participation_repository.get_scores(),
        }, 200

    @app.route('/questions/<int:question_id>', methods=['GET'])
    def get_quiz_by_id(question_id):
        """Obtenir une question et ses choix par identifiant.
        ---
        tags:
        - Questions
        parameters:
        - name: question_id
          in: path
          required: true
          type: integer
          description: Identifiant de la question.
        responses:
          '200':
            description: Question avec ses choix classés par identifiant croissant.
            schema:
              $ref: '#/definitions/Question'
          '404':
            $ref: '#/responses/QuestionNotFound'
        """
        question = repository.get_byid(question_id)

        if question is None:
            return {"error": "Question introuvable"}, 404

        question["possibleAnswers"] = [
            possible_answer_to_json(answer)
            for answer in answer_repository.get_by_question_id(question["id"])
        ]
        return question, 200

    @app.route('/questions', methods=['GET'])
    def get_quiz_by_position():
        """Obtenir une question et ses choix par position.
        ---
        tags:
        - Questions
        parameters:
        - name: position
          in: query
          required: true
          type: integer
          minimum: 1
          description: Position de la question dans le quiz, à partir de 1.
        responses:
          '200':
            description: Question avec ses choix classés par identifiant croissant.
            schema:
              $ref: '#/definitions/Question'
          '400':
            $ref: '#/responses/InvalidInput'
          '404':
            $ref: '#/responses/QuestionNotFound'
        """
        position = request.args.get("position", type=int)

        if position is None or position < 1:
            return {"error": "Une position entière positive est attendue"}, 400

        question = repository.get_by_position(position)

        if question is None:
            return {"error": "Question introuvable"}, 404

        question["possibleAnswers"] = [
            possible_answer_to_json(answer)
            for answer in answer_repository.get_by_question_id(question["id"])
        ]
        return question, 200
    

    ### POST 
    @app.route("/login", methods=["POST"])
    def post_login():
        """Obtenir un jeton JWT avec le mot de passe administrateur.
        ---
        tags:
        - Authentification
        consumes:
        - application/json
        parameters:
        - name: body
          in: body
          required: true
          schema:
            type: object
            required:
            - password
            properties:
              password:
                type: string
                format: password
                description: Mot de passe administrateur configuré sur le serveur.
        responses:
          '200':
            description: Jeton à envoyer dans Authorization avec le préfixe Bearer.
            schema:
              type: object
              required:
              - size
              - credentials
              - token
              properties:
                size:
                  type: integer
                  example: 0
                credentials:
                  type: array
                  items:
                    type: string
                  description: Hash du mot de passe renvoyé par l'implémentation actuelle.
                token:
                  type: string
                  description: Jeton JWT signé avec une date d'expiration.
          '401':
            description: Mot de passe erroné.
            schema:
              $ref: '#/definitions/Error'
          '500':
            description: Le code actuel échoue si le corps JSON ou le mot de passe est absent ou de type incorrect.
        """
        payload = request.get_json(silent=True)
    
        password = payload.get("password")
        hashed_pass = HashGen(password)

        if not isinstance(password, str) or password != ADMIN_PASS:
            return {"error": "Mot de passe erroné"}, 401
        
        token = jwt_service.build({"password": hashed_pass})

        return {"size": 0, "credentials": [hashed_pass], "token": token}, 200

    @app.route("/questions", methods=["POST"])
    @jwt_service.required
    def post_question():
        """Créer une question et ses choix.
        ---
        tags:
        - Questions
        security:
        - BearerAuth: []
        consumes:
        - application/json
        description: Insère la question à la position demandée et décale les questions suivantes. Enregistre ensuite
          les choix.
        parameters:
        - name: body
          in: body
          required: true
          schema:
            $ref: '#/definitions/QuestionInput'
        responses:
          '200':
            description: Question créée avec son identifiant.
            schema:
              $ref: '#/definitions/QuestionCreated'
          '400':
            $ref: '#/responses/InvalidInput'
          '401':
            $ref: '#/responses/Unauthorized'
          '500':
            description: Erreur d'insertion ou choix absents ou mal formés. La question peut déjà avoir été enregistrée.
        """
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
        """Ajouter des choix à une question.
        ---
        tags:
        - Questions
        description: Ajoute les choix transmis. La méthode QuestionRepository.add_possible_answers appelée par
          cette route est actuellement absente du dépôt.
        consumes:
        - application/json
        parameters:
        - name: question_id
          in: path
          required: true
          type: integer
          description: Identifiant de la question.
        - name: body
          in: body
          required: true
          schema:
            type: object
            required:
            - possibleAnswers
            properties:
              possibleAnswers:
                type: array
                minItems: 1
                items:
                  $ref: '#/definitions/PossibleAnswer'
        responses:
          '200':
            description: Question et liste des choix après ajout, lorsque la méthode du dépôt est disponible.
            schema:
              type: object
              required:
              - id
              - possibleAnswers
              properties:
                id:
                  type: integer
                possibleAnswers:
                  type: array
                  items:
                    $ref: '#/definitions/PossibleAnswer'
          '400':
            $ref: '#/responses/InvalidInput'
          '404':
            $ref: '#/responses/QuestionNotFound'
          '500':
            description: Méthode add_possible_answers absente du dépôt actuel.
        """
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
        """Calculer et enregistrer une participation.
        ---
        tags:
        - Participations
        consumes:
        - application/json
        description: Les réponses suivent les questions par position croissante. Chaque entier désigne un choix
          à partir de 1, les choix étant classés par identifiant croissant. Le serveur calcule le score.
        parameters:
        - name: body
          in: body
          required: true
          schema:
            type: object
            required:
            - playerName
            - answers
            properties:
              playerName:
                type: string
                example: Lucas
              answers:
                type: array
                items:
                  type: integer
                  minimum: 1
                example:
                - 3
                - 1
                - 2
        responses:
          '200':
            description: Nom du joueur et score enregistrés.
            schema:
              $ref: '#/definitions/Participation'
          '400':
            description: Nom ou réponses invalides, nombre de réponses incorrect ou numéro de choix invalide.
            schema:
              $ref: '#/definitions/Error'
        """
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
        """Réinitialiser la base depuis database.sql.
        ---
        tags:
        - Administration
        security:
        - BearerAuth: []
        description: Supprime les questions, les choix et les participations, puis recrée les tables à partir
          de database.sql.
        produces:
        - text/html
        responses:
          '200':
            description: Corps contenant exactement Ok.
            schema:
              type: string
              example: Ok
          '401':
            $ref: '#/responses/Unauthorized'
          '500':
            description: Fichier SQL inaccessible ou échec de l'exécution du script.
        """
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
        """Modifier une question, sa position et ses choix.
        ---
        tags:
        - Questions
        security:
        - BearerAuth: []
        consumes:
        - application/json
        description: Remplace les champs et tous les choix. Une position modifiée décale les questions intermédiaires.
          La position attendue est comprise entre 1 et la position maximale actuelle.
        parameters:
        - name: question_id
          in: path
          required: true
          type: integer
          description: Identifiant de la question.
        - name: body
          in: body
          required: true
          schema:
            $ref: '#/definitions/QuestionInput'
        responses:
          '204':
            description: Question et choix modifiés. Corps vide.
          '400':
            $ref: '#/responses/InvalidInput'
          '401':
            $ref: '#/responses/Unauthorized'
          '404':
            $ref: '#/responses/QuestionNotFound'
          '500':
            description: Le code actuel laisse remonter ValueError si la position est hors limites ou de type
              incorrect.
        """
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
        """Supprimer une question et ses choix.
        ---
        tags:
        - Questions
        security:
        - BearerAuth: []
        description: Supprime la question et ses choix, puis diminue de 1 les positions suivantes.
        parameters:
        - name: question_id
          in: path
          required: true
          type: integer
          description: Identifiant de la question.
        responses:
          '204':
            description: Question et choix supprimés, positions resserrées. Corps vide.
          '401':
            $ref: '#/responses/Unauthorized'
          '404':
            $ref: '#/responses/QuestionNotFound'
        """
        deleted = repository.delete(question_id)

        if not deleted:
            return {"error": "Question introuvable"}, 404

        return "", 204


    @app.route("/questions/all", methods=["DELETE"])
    @jwt_service.required
    def delete_all_questions():
        """Supprimer toutes les questions et leurs choix.
        ---
        tags:
        - Questions
        security:
        - BearerAuth: []
        responses:
          '204':
            description: Toutes les questions et leurs choix ont été supprimés. Corps vide.
          '401':
            $ref: '#/responses/Unauthorized'
        """
        repository.delete_all()
        return "", 204


    @app.route("/participations/all", methods=["DELETE"])
    @jwt_service.required
    def delete_all_participants():
        """Supprimer toutes les participations.
        ---
        tags:
        - Participations
        security:
        - BearerAuth: []
        responses:
          '204':
            description: Toutes les participations ont été supprimées. Corps vide.
          '401':
            $ref: '#/responses/Unauthorized'
        """
        participation_repository.delete_all()
        return "", 204

    
    return app
