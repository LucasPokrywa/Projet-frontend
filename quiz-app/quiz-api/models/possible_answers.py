import sqlite3
from contextlib import closing
from dataclasses import dataclass


@dataclass
class PossibleAnswer:
    question_id: int
    position: int
    text: str
    is_correct: bool


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
