from peewee import *

db = SqliteDatabase('S6.db')

class BaseModel(Model):
    class Meta:
        database = db

class Specialization(BaseModel):
    code = CharField(primary_key=True)
    name = CharField()
    duration_training = IntegerField()
    department_id = IntegerField()
    is_active = BooleanField(default=True)

def createTable():
    db.create_tables([Specialization])

if __name__ == '__main__':
    createTable()
