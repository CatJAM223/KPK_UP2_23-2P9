from peewee import SqliteDatabase, Model, PrimaryKeyField, CharField, BooleanField

# Инициализация базы данных
db = SqliteDatabase("disciplines.db")


class BaseModel(Model):
    class Meta:
        database = db


class Discipline(BaseModel):
    """Модель справочника дисциплин (Discipline Service)"""

    id = PrimaryKeyField()
    name = CharField(max_length=255, null=False)
    code = CharField(max_length=255, null=False)
    is_active = BooleanField(default=True)

    class Meta:
        # Составной уникальный индекс для комбинации name и code
        indexes = ((("name", "code"), True),)


def init_db():
    """Функция для создания таблиц"""
    db.connect()
    db.create_tables([Discipline], safe=True)


if __name__ == "__main__":
    init_db()
