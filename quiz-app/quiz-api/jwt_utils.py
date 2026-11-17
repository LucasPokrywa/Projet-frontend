import jwt
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone


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
