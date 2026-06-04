from peewee import *

db = SqliteDatabase('S7.db')

class BaseModel(Model):
    class Meta:
        database = db

class Group(BaseModel):
    year_create = IntegerField()
    number = IntegerField()
    prefix = CharField()
    code = CharField()
    class_number = IntegerField()
    tutor_id = IntegerField(null=True)
    is_active = BooleanField(default=True)
    
    class Meta:
        indexes = ((('year_create', 'number', 'prefix', 'class_number'), True),)

class Student(BaseModel):
    id_student = AutoField()  # Исправлено: AutoField вместо PrimaryKeyField
    id_group = ForeignKeyField(Group, backref='students')

def init_db():
    """Функция для создания таблиц"""
    db.create_tables([Group, Student])

if __name__ == "__main__":
    init_db()
