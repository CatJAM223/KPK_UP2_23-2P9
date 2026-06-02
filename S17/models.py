from peewee import *

db = SqliteDatabase('rooms.db')


def init_db():
    db.connect()
    db.create_tables([Building, Room, Equipment, RoomEquipment], safe=True)
    db.close()


class Building(Model):
    id = AutoField()
    name = CharField(max_length=100, unique=True, null=False)
    address = CharField(max_length=255, null=False)
    floors_count = IntegerField(null=False)

    class Meta:
        database = db
        table_name = 'buildings'


class Room(Model):
    id = AutoField()
    number = CharField(max_length=20, null=False)
    floor = IntegerField(null=False)
    capacity = IntegerField(null=False)
    building_id = ForeignKeyField(Building, backref='rooms', on_delete='CASCADE', null=False)
    has_computers = BooleanField(default=False, null=False)
    is_active = BooleanField(default=True, null=False)

    class Meta:
        database = db
        table_name = 'rooms'
        indexes = ((('number', 'building_id'), True),)

    def save(self, *args, **kwargs):
        if self.floor < -2 or self.floor > 25:
            raise ValueError('floor должен быть от -2 до 25')
        if self.capacity < 1 or self.capacity > 500:
            raise ValueError('capacity должен быть от 1 до 500')
        super().save(*args, **kwargs)


class Equipment(Model):
    id = AutoField()
    name = CharField(max_length=100, unique=True, null=False)
    description = TextField(null=True)

    class Meta:
        database = db
        table_name = 'equipments'


class RoomEquipment(Model):
    id = AutoField()
    room = ForeignKeyField(Room, backref='equipment_items', on_delete='CASCADE', null=False)
    equipment = ForeignKeyField(Equipment, backref='room_items', on_delete='CASCADE', null=False)
    quantity = IntegerField(default=1, null=False)

    class Meta:
        database = db
        table_name = 'room_equipment'
        indexes = ((('room', 'equipment'), True),)
