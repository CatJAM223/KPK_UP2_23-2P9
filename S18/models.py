from peewee import (
    SqliteDatabase, Model, AutoField, CharField,
    IntegerField, BooleanField, ForeignKeyField, Check
)


db = SqliteDatabase("database.db")


class BaseModel(Model):
    class Meta:
        database = db


class Equipment(BaseModel):
    id = AutoField()
    name = CharField(null=False)
    is_active = BooleanField(default=True)


class RoomEquipment(BaseModel):
    id = AutoField()
    room_id = IntegerField(constraints=[Check('room_id > 0')])
    equipment = ForeignKeyField(Equipment, backref='room_equipment')
    is_active = BooleanField(default=True)


if __name__ == "__main__":
    db.create_tables([Equipment, RoomEquipment])
