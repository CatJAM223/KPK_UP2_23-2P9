from peewee import *
from datetime import date, datetime

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
    tutor_id = IntegerField(default=None, null=True)
    is_active = BooleanField(default=True)
    count_student = IntegerField(default=0)
    
    class Meta:
        indexes = ((('year_create', 'number', 'prefix', 'class_number'), True),)

    @staticmethod
    def get_course_number(admission_year):
        current_date = date.today()
        current_year = current_date.year
        current_month = current_date.month
        
        if current_month >= 9:
            current_academic_year = current_year
        else:
            current_academic_year = current_year - 1
        if admission_year > current_academic_year:
            return None
        
        course = current_academic_year - admission_year + 1
        
        return course

    @property
    def name(self) -> str:
        course = Group.get_course_number(self.year_create)
        return f"{course}-{self.number}{self.prefix}{self.class_number}"

class Student(BaseModel):
    id_student = IntegerField()
    id_group = ForeignKeyField(Group, backref='students')

def createTable():
    db.create_tables([Group, Student])

if __name__ == '__main__':
    createTable()