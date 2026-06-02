from peewee import *
from datetime import date

db = SqliteDatabase('S7.db')

class BaseModel(Model):
    class Meta:
        database = db

class Group(BaseModel):
    id = AutoField()
    year_create = IntegerField()
    number = IntegerField()
    prefix = CharField()
    code = CharField()
    class_number = IntegerField()
    tutor_id = IntegerField(null=True, default=None)
    is_active = BooleanField(default=True)
    
    class Meta:
        table_name = 'groups'
        indexes = (
            (('year_create', 'number', 'prefix', 'class_number'), True),
            (('tutor_id',), False),
            (('code',), False),
        )
    
    @property
    def name(self) -> str:
        """Вычисляемое наименование группы"""
        from app.services import get_course_number
        course = get_course_number(self.year_create)
        return f"{course}-{self.number}{self.prefix}{self.class_number}"
    
    def soft_delete(self) -> bool:
        """Мягкое удаление группы"""
        if not self.is_active:
            return False
        self.is_active = False
        self.save()
        return True

class Student(BaseModel):
    id_student = IntegerField(primary_key=True, unique=True)
    id_group = ForeignKeyField(Group, backref='students', on_delete='CASCADE')
    
    class Meta:
        table_name = 'students'

def create_tables():
    db.create_tables([Group, Student])

if __name__ == '__main__':
    create_tables()
