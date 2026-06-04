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
    tutor_id = IntegerField(null=True)  # NULL для отсутствующего куратора
    is_active = BooleanField(default=True)
    # count_student - убрал, так как это вычисляемое поле
    
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
    
    @property
    def count_student(self) -> int:
        """Вычисляемое поле - количество студентов в группе"""
        return self.students.count()

class Student(BaseModel):
    id_student = IntegerField(primary_key=True)  # Добавил primary_key=True
    id_group = ForeignKeyField(Group, backref='students')

def init_db():
    """Функция для создания таблиц"""
    db.create_tables([Group, Student])

if __name__ == '__main__':
    init_db()
