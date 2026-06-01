import re
from peewee import *

db = SqliteDatabase('S2_Profile_datebase.db')

class BaseModel(Model):
    class Meta:
        database = db

class Profile(BaseModel):
    full_name = CharField()
    telephone = CharField(max_length=10, unique=True)
    email = CharField(max_length=254, unique=True)
    path_to_photo = CharField()
    is_active = BooleanField(default=True)

class NotificationSettings(BaseModel):
    profile_id = ForeignKeyField(Profile, backref='notification_settings')
    parameter = CharField()
    value = CharField()

if __name__ == '__main__':
    db.create_tables([Profile, NotificationSettings])
