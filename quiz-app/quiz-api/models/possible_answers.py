import sqlite3
from contextlib import closing
from dataclasses import dataclass


@dataclass
class PossibleAnswer:
    question_id: int
    text: str
    is_correct: bool


def possible_answer_from_json(data, question_id):
    return PossibleAnswer(
        question_id=question_id,
        text=data["text"],
        is_correct=data["isCorrect"],
    )


def possible_answer_to_json(answer):
    return {
        "text": answer.text,
        "isCorrect": bool(answer.is_correct),
    }


class PossibleAnswerRepository:
    def __init__(self, path):
        self.path = path

    def insert(self, question_id, answer):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            with connection:
                connection.execute(
                    """
                    INSERT INTO possible_answers (
                        question_id, text, is_correct
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        question_id,
                        answer.text,
                        int(answer.is_correct),
                    ),
                )
