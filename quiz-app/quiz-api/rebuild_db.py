from pathlib import Path
from models.questions import QuestionRepository


if __name__ == "__main__":
    database_path = Path(__file__).resolve().with_name("database")

    if not database_path.exists():
        repository = QuestionRepository(database_path)
        repository.rebuild()
        print("Base SQLite créée")
    else:
        print("La base SQLite existe déjà")