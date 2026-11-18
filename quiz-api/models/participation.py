import sqlite3
from contextlib import closing
from dataclasses import dataclass


@dataclass
class Participation:
    player_name: str
    score: int
    id: int | None = None


def participation_from_json(data):
    return Participation(
        player_name=data["playerName"],
        score=data["score"],
    )


def participation_to_json(participation):
    data = {
        "playerName": participation.player_name,
        "score": participation.score,
    }
    if participation.id is not None:
        data["id"] = participation.id
    return data


class ParticipationRepository:
    def __init__(self, path):
        self.path = path

    def insert(self, participation):
        with closing(sqlite3.connect(self.path)) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    INSERT INTO participation (player_name, score)
                    VALUES (?, ?)
                    """,
                    (participation.player_name, participation.score),
                )
                participation_id = cursor.lastrowid

        participation.id = participation_id
        return participation_id

    def delete_all(self):
        with closing(sqlite3.connect(self.path)) as connection:
            with connection:
                connection.execute("DELETE FROM participation")

    def calculate_score(self, answers):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("BEGIN")

            questions = connection.execute(
                "SELECT id FROM questions ORDER BY position"
            ).fetchall()

            if len(answers) != len(questions):
                raise ValueError(
                    f"{len(questions)} réponses attendues, {len(answers)} reçues"
                )

            score = 0

            for (question_id,), choice_number in zip(questions, answers):
                choices = connection.execute(
                    """
                    SELECT is_correct FROM possible_answers
                    WHERE question_id = ?
                    ORDER BY id
                    """,
                    (question_id,),
                ).fetchall()

                if (
                    type(choice_number) is not int
                    or not 1 <= choice_number <= len(choices)
                ):
                    raise ValueError(
                        f"Choix invalide pour la question {question_id}"
                    )

                if choices[choice_number - 1][0] == 1:
                    score += 1

        return score
    

    def get_scores(self):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT player_name AS playerName, score
                FROM participation
                ORDER BY score DESC, id ASC
                """
            ).fetchall()

        return [dict(row) for row in rows]