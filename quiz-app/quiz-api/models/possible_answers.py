import sqlite3
from contextlib import closing
from dataclasses import dataclass


@dataclass
class PossibleAnswer:
    question_id: int
    position: int
    text: str
    is_correct: bool


def possible_answer_from_json(data, question_id, position):
    return PossibleAnswer(
        question_id=question_id,
        position=position,
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

    def insert(self, answer):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            with connection:
                connection.execute(
                    """
                    INSERT INTO possible_answers (
                        question_id, position, text, is_correct
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        answer.question_id,
                        answer.position,
                        answer.text,
                        int(answer.is_correct),
                    ),
                )
