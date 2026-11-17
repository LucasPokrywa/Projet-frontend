import sqlite3
from contextlib import closing
import json

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
                connection.execute("BEGIN IMMEDIATE")

                questions_to_shift = connection.execute(
                    """
                    SELECT id
                    FROM questions
                    WHERE position >= ?
                    ORDER BY position DESC
                    """,
                    (question.position,),
                ).fetchall()

                connection.executemany(
                    "UPDATE questions SET position = position + 1 WHERE id = ?",
                    questions_to_shift,
                )

                cursor = connection.execute(
                    """
                    INSERT INTO questions (position, title, text, image)
                    VALUES (?, ?, ?, ?)
                    """,
                    (question.position, question.title, question.text, question.image),
                )
                question_id = cursor.lastrowid

        return question_id

    
    def get_byid(self, question_id):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT * FROM questions WHERE id = ?",
                (question_id,),
            ).fetchone()

        if row is None:
            return None
        
        question = dict(row)
        return question

    def get_by_position(self, position):
            with closing(sqlite3.connect(self.path)) as connection:
                connection.row_factory = sqlite3.Row
                row = connection.execute(
                    "SELECT * FROM questions WHERE position = ?",
                    (position,),
                ).fetchone()
    
            if row is None:
                return None
            
            question = dict(row)
            return question
    

    def delete(self, question_id):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")

            with connection:
                deleted = connection.execute(
                    """
                    DELETE FROM questions
                    WHERE id = ?
                    RETURNING position
                    """,
                    (question_id,),
                ).fetchone()

                if deleted is None:
                    return False

                (position,) = deleted
                connection.execute(
                    """
                    UPDATE questions
                    SET position = position - 1
                    WHERE position > ?
                    """,
                    (position,),
                )

        return True

    def update(self, question_id, question, answers):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")

            with connection:
                cursor = connection.execute(
                    """
                    UPDATE questions
                    SET title = ?, text = ?, image = ?
                    WHERE id = ?
                    """,
                    (question.title, question.text, question.image, question_id),
                )

                if cursor.rowcount == 0:
                    return False
    
                connection.execute(
                    "DELETE FROM possible_answers WHERE question_id = ?",
                    (question_id,),
                )

                for answer in answers:
                    connection.execute(
                        """
                        INSERT INTO possible_answers (question_id, text, is_correct)
                        VALUES (?, ?, ?)
                        """,
                        (question_id, answer.text, int(answer.is_correct)),
                    )

        return True