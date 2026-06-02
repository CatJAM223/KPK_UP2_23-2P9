from peewee import *
from datetime import date

db = SqliteDatabase('S9.db')

class BaseModel(Model):
    class Meta:
        database = db


class OrderType(BaseModel):
    """Тип приказа (справочник)"""
    name = CharField(max_length=50, unique=True, null=False)
    is_active = BooleanField(default=True, null=False)


class OrderDocument(BaseModel):
    """Содержание приказа"""
    order_type = ForeignKeyField(OrderType, backref='documents', null=False)
    order_number = CharField(max_length=50, null=False) 
    order_date = DateField(null=False)
    signed_by = CharField(max_length=100, null=False)
    is_active = BooleanField(default=True, null=False)

    class Meta:
        constraints = [SQL('UNIQUE(order_type_id, order_number)')]


class OrderDocumentStudent(BaseModel):
    """Транзитивная таблица для связи """
    order_document = ForeignKeyField(OrderDocument, backref='student_links', null=False)
    student_id = IntegerField(null=False)  # ID из сервиса 7

    class Meta:
        constraints = [SQL('UNIQUE(order_document_id, student_id)')]


def createTable():
    """Создаёт таблицы в базе данных"""
    db.create_tables([OrderType, OrderDocument, OrderDocumentStudent])


def add_default_order_types():
    """Добавляет стандартные типы приказов"""
    default_types = [
        'Отчисление',
        'Перевод',
        'Восстановление',
        'Академический отпуск',
        'Выход из отпуска',
    ]
    for name in default_types:
        OrderType.get_or_create(name=name)


if __name__ == '__main__':
    createTable()
    add_default_order_types()
