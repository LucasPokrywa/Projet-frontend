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
