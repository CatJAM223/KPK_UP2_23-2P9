from peewee import *

db = SqliteDatabase('S4.db')

class BaseModel(Model):
    class Meta:
        database = db

class Permission(BaseModel):
    role_id = IntegerField(constraints=[Check('role_id BETWEEN 1 AND 6')])
    method = CharField(constraints=[Check("method IN ('GET','HEAD','OPTIONS','POST', 'PUT', 'PATCH', 'TRACE','CONNECT','DELETE')")])
    url = CharField()


def init_db():
    db.create_tables([Permission])

if __name__ == '__main__':
    init_db()