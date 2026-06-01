import os
from peewee import (
    Model,
    SqliteDatabase,
    IntegerField,
    BooleanField
)

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")
db = SqliteDatabase(DB_PATH, pragmas={"foreign_keys": 0})  # FK отключены


class BaseModel(Model):
    class Meta:
        database = db


class Assignment(BaseModel):
    teacher_id = IntegerField(null=False)      # ID из Teacher Service
    group_id = IntegerField(null=False)        # ID из Group Service
    discipline_id = IntegerField(null=False)   # ID из Discipline Service
    hours = IntegerField(null=False)           # Количество часов нагрузки
    is_active = BooleanField(default=True)

    class Meta:
        # Составной уникальный индекс для предотвращения дублирования связей
        indexes = (
            (("teacher_id", "group_id", "discipline_id"), True),
        )


def init_db():
    db.connect(reuse_if_open=True)
    db.create_tables([Assignment], safe=True)
    db.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
