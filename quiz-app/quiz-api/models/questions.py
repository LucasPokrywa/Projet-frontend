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

    def insert(self, question, answers=None):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
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

                if answers is not None:
                    connection.executemany(
                        """
                        INSERT INTO possible_answers (question_id, text, is_correct)
                        VALUES (?, ?, ?)
                        """,
                        [
                            (question_id, answer["text"], int(answer["isCorrect"]))
                            for answer in answers
                        ],
                    )

        return question_id

    
    def add_possible_answers(self, question_id, answers):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")

            with connection:
                connection.execute("BEGIN IMMEDIATE")
                question = connection.execute(
                    "SELECT id FROM questions WHERE id = ?",
                    (question_id,),
                ).fetchone()

                if question is None:
                    return None

                connection.executemany(
                    """
                    INSERT INTO possible_answers (question_id, text, is_correct)
                    VALUES (?, ?, ?)
                    """,
                    [
                        (question_id, answer["text"], int(answer["isCorrect"]))
                        for answer in answers
                    ],
                )
                rows = connection.execute(
                    """
                    SELECT text, is_correct FROM possible_answers
                    WHERE question_id = ? ORDER BY id
                    """,
                    (question_id,),
                ).fetchall()

        return [{"text": text, "isCorrect": bool(correct)} for text, correct in rows]

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
                connection.execute("BEGIN IMMEDIATE")

                row = connection.execute(
                    "SELECT position FROM questions WHERE id = ?",
                    (question_id,),
                ).fetchone()

                if row is None:
                    return False

                old_position = row[0]
                new_position = question.position

                max_position = connection.execute(
                    "SELECT MAX(position) FROM questions"
                ).fetchone()[0]

                if (
                    type(new_position) is not int
                    or not 1 <= new_position <= max_position
                ):
                    raise ValueError(
                        f"La position doit être entre 1 et {max_position}"
                    )

                if new_position != old_position:
                    # Libère temporairement la position actuelle.
                    connection.execute(
                        "UPDATE questions SET position = ? WHERE id = ?",
                        (max_position + 1, question_id),
                    )

                    questions_to_shift = connection.execute(
                        """
                        SELECT id FROM questions
                        WHERE position BETWEEN ? AND ?
                        ORDER BY position ASC
                        """,
                        (
                            min(old_position, new_position),
                            max(old_position, new_position),
                        ),
                    ).fetchall()

                    offset = -1

                    if new_position < old_position:
                        questions_to_shift.reverse()
                        offset = 1

                    for (other_id,) in questions_to_shift:
                        connection.execute(
                            """
                            UPDATE questions
                            SET position = position + ?
                            WHERE id = ?
                            """,
                            (offset, other_id),
                        )

                connection.execute(
                    """
                    UPDATE questions
                    SET position = ?, title = ?, text = ?, image = ?
                    WHERE id = ?
                    """,
                    (
                        new_position,
                        question.title,
                        question.text,
                        question.image,
                        question_id,
                    ),
                )

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

    
    def delete(self, question_id):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")

            with connection:
                connection.execute("BEGIN IMMEDIATE")

                row = connection.execute(
                    "SELECT position FROM questions WHERE id = ?",
                    (question_id,),
                ).fetchone()

                if row is None:
                    return False

                position = row[0]

                connection.execute(
                    "DELETE FROM possible_answers WHERE question_id = ?",
                    (question_id,),
                )
                connection.execute(
                    "DELETE FROM questions WHERE id = ?",
                    (question_id,),
                )

                following_questions = connection.execute(
                    """
                    SELECT id FROM questions
                    WHERE position > ?
                    ORDER BY position ASC
                    """,
                    (position,),
                ).fetchall()

                for (following_id,) in following_questions:
                    connection.execute(
                        "UPDATE questions SET position = position - 1 WHERE id = ?",
                        (following_id,),
                    )

        return True


    def delete_all(self):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")

            with connection:
                connection.execute("DELETE FROM possible_answers")
                connection.execute("DELETE FROM questions")


    
    def count(self):
        with closing(sqlite3.connect(self.path)) as connection:
            return connection.execute(
                "SELECT COUNT(*) FROM questions"
            ).fetchone()[0]
