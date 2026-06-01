import os
from peewee import *
from datetime import datetime

# Инициализация базы данных
db = SqliteDatabase('work_program.db')

class BaseModel(Model):
    class Meta:
        database = db

class Discipline(BaseModel):
    """Модель дисциплины (для связи)"""
    name = CharField(max_length=200, unique=True)
    code = CharField(max_length=20, unique=True)
    is_deleted = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

class Specialty(BaseModel):
    """Модель специальности (для связи)"""
    code = CharField(max_length=20, unique=True)
    name = CharField(max_length=200)
    fgos_standard = CharField(max_length=50)
    is_deleted = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

class WorkProgram(BaseModel):
    """Модель рабочей программы"""
    discipline = ForeignKeyField(Discipline, backref='work_programs', on_delete='RESTRICT', null=False)
    specialty = ForeignKeyField(Specialty, backref='work_programs', on_delete='RESTRICT', null=False)
    file_path = CharField(max_length=500, null=False)
    semester = IntegerField(null=False, constraints=[Check('semester BETWEEN 1 AND 8')])
    lecture_hours = IntegerField(default=0, null=False, constraints=[Check('lecture_hours >= 0')])
    practice_hours = IntegerField(default=0, null=False, constraints=[Check('practice_hours >= 0')])
    lab_hours = IntegerField(default=0, null=False, constraints=[Check('lab_hours >= 0')])
    exam_form = CharField(max_length=20, default='credit', null=False, constraints=[Check("exam_form IN ('exam', 'credit', 'coursework')")])
    is_deleted = BooleanField(default=False, null=False)
    created_at = DateTimeField(default=datetime.now, null=False)
    updated_at = DateTimeField(default=datetime.now, null=False)

    class Meta:
        indexes = (
            (('discipline', 'specialty', 'semester'), True),  # уникальная комбинация
        )

    @property
    def total_hours(self):
        return self.lecture_hours + self.practice_hours + self.lab_hours

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)

def init_db():
    """Инициализация базы данных"""
    db.connect()
    db.create_tables([Discipline, Specialty, WorkProgram], safe=True)
    
    # Заполнение тестовыми данными (для проверки)
    if not Discipline.select().exists():
        disc1 = Discipline.create(name='Математика', code='MATH101')
        disc2 = Discipline.create(name='Физика', code='PHYS101')
        
        spec1 = Specialty.create(code='09.02.07', name='Информационные системы', fgos_standard='ФГОС СПО 2022')
        spec2 = Specialty.create(code='38.02.01', name='Экономика', fgos_standard='ФГОС СПО 2022')
        
        WorkProgram.create(
            discipline=disc1,
            specialty=spec1,
            file_path='/files/math_work_program.pdf',
            semester=1,
            lecture_hours=32,
            practice_hours=32,
            lab_hours=0,
            exam_form='exam'
        )
        WorkProgram.create(
            discipline=disc2,
            specialty=spec2,
            file_path='/files/physics_work_program.pdf',
            semester=2,
            lecture_hours=32,
            practice_hours=16,
            lab_hours=16,
            exam_form='credit'
        )
    
    print("База данных инициализирована")
    db.close()

# Точка входа для инициализации
if __name__ == '__main__':
    init_db()
