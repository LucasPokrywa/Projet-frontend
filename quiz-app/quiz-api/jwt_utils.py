import jwt
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request

load_dotenv()

class JwtError(Exception):
    """Exception raised for jwt errors in the quizz app
    """

    def __init__(self, message="Jwt error"):
        self.message = message
        super().__init__(self.message)

class JWToken:
    """ Classe JWT pour créer et décoder des tokens
    """
    ALGORITHM = "HS256"

    def __init__(self):
        self.secret_key = os.environ["JWT_SECRET"]
        self.lifetime = timedelta(minutes=int(os.environ["JWT_DURATION"]))
        return

    def build(self, data):
        now = datetime.now(timezone.utc)

        payload = {
            "data": data,
            "iat": now,
            "exp": now + self.lifetime,
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.ALGORITHM)

    def decode(self, token):
        return jwt.decode(
            token,
            self.secret_key,
            algorithms=[self.ALGORITHM],
            options={"require": ["data", "iat", "exp"]},
        )

    def required(self, function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            parts = request.headers.get("Authorization", "").split()

            if len(parts) != 2 or parts[0].lower() != "bearer":
                return {"error": "Token manquant"}, 401

            try:
                self.decode(parts[1])
            except jwt.InvalidTokenError:
                return {"error": "Token invalide ou expiré"}, 401

            return function(*args, **kwargs)

        return wrapper