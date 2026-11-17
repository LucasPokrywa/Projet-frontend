import sqlite3
from contextlib import closing


class Question:
    def __init__(self, position, title, text, image):
        self.position = position
        self.title = title
        self.text = text
        self.image = image


def question_from_json(data):
    return Question(
        position=data["position"],
        title=data["title"],
        text=data["text"],
        image=data["image"],
    )


def question_to_json(question):
    return {
        "position": question.position,
        "title": question.title,
        "text": question.text,
        "image": question.image,
    }


class QuestionRepository:
    def __init__(self, path):
        self.path = path

    def insert(self, question):
        with closing(sqlite3.connect(self.path)) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    INSERT INTO Question (position, title, text, image)
                    VALUES (?, ?, ?, ?)
                    """,
                    (question.position, question.title, question.text, question.image),
                )
                question_id = cursor.lastrowid

        return question_id