import sqlite3
from contextlib import closing
import json

class Question:
    def __init__(self, position, title, text, image, possibleAnswers):
        self.position = position
        self.title = title
        self.text = text
        self.image = image
        self.possibleAnswers = possibleAnswers


def question_from_json(data):
    return Question(
        position=data["position"],
        title=data["title"],
        text=data["text"],
        image=data["image"],
        possibleAnswers=data["possibleAnswers"],
    )


def question_to_json(question):
    return {
        "position": question.position,
        "title": question.title,
        "text": question.text,
        "image": question.image,
        "possibleAnswers": question.possibleAnswers,
    }


class QuestionRepository:
    def __init__(self, path):
        self.path = path

    def insert(self, question):
        with closing(sqlite3.connect(self.path)) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    INSERT INTO Question (position, title, text, image, possibleAnswers)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (question.position, question.title, question.text, question.image, json.dumps(question.possibleAnswers, ensure_ascii=False),),
                )
                question_id = cursor.lastrowid

        return question_id

    def get_byid(self, question_id):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT * FROM Question WHERE id = ?",
                (question_id,),
            ).fetchone()

        if row is None:
            return None
        
        question = dict(row)
        question["possibleAnswers"] = json.loads(question["possibleAnswers"])
        return question
