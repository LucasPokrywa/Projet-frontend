from flask import Flask
from flask_cors import CORS
from flask import request

from hash import HashGen, HashCompare
from jwt_utils import JWToken


app = Flask(__name__)
CORS(app)
jwt_service = JWToken()

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

if __name__ == "__main__":
    app.run()
