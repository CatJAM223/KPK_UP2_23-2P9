from peewee import *

db = SqliteDatabase('auth.db')

class User(Model):
    login = CharField(unique=True, max_length=50)
    password_hash = CharField()
    is_active = BooleanField(default=True)

    class Meta:
        database = db

def init_db():
    db.connect()
    db.create_tables([User], safe=True)
    db.close()

if __name__ == '__main__':
    init_db()
