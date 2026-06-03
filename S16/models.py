from peewee import *

db = SqliteDatabase("campus.db")

class BaseModel(Model):
    class Meta:
        database = db

class Building(BaseModel):
    name = CharField(max_length=100, null=False)
    address = CharField(max_length=255, null=False)
    floors = IntegerField(constraints=[Check("floors > 0")], null=False)
    is_active = BooleanField(default=True, null=False)

    class Meta:
        indexes = (
            (("name", "address"), True),
        ) 

def init_db():
    db.connect()
    db.create_tables([Building], safe=True)
    db.close()

if __name__ == "__main__":
    init_db()
