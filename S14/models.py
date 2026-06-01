from peewee import *


db = SqliteDatabase('S14.db')


class BaseModel(Model):
    class Meta:
        database = db


class Teacher(BaseModel):
    """Преподаватель"""
    name = CharField(max_length=100, null=False)
    department = CharField(max_length=50, null=False)
    is_active = BooleanField(default=True, null=False)


class Curriculum(BaseModel):
    """Учебный план"""
    course_name = CharField(max_length=100, null=False)
    total_hours = IntegerField(null=False, constraints=[Check('total_hours > 0')])
    is_active = BooleanField(default=True, null=False)


class Group(BaseModel):
    """Группа"""
    curriculum = ForeignKeyField(Curriculum, backref='groups', null=False)
    name = CharField(max_length=50, null=False)
    semester = IntegerField(null=False, constraints=[Check('semester >= 1 AND semester <= 12')])
    is_active = BooleanField(default=True, null=False)

    class Meta:
        constraints = [SQL('UNIQUE(curriculum_id, name, semester)')]


class TeacherGroup(BaseModel):
    """Транзитивная таблица для связи преподавателей и групп"""
    teacher = ForeignKeyField(Teacher, backref='group_links', null=False)
    group = ForeignKeyField(Group, backref='teacher_links', null=False)
    assigned_hours = IntegerField(null=False, constraints=[Check('assigned_hours >= 0')])
    is_active = BooleanField(default=True, null=False)

    class Meta:
        constraints = [SQL('UNIQUE(teacher_id, group_id)')]


def createTable():
    """Создаёт таблицы в базе данных"""
    db.create_tables([Teacher, Curriculum, Group, TeacherGroup])


if __name__ == '__main__':
    createTable()
