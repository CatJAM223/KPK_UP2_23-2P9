from peewee import *
from datetime import date, datetime

db = SqliteDatabase('S8.db')

class BaseModel(Model):
    class Meta:
        database = db


class Subgroup(BaseModel):
    id_subgroup = AutoField() 
    id_group = IntegerField()
    subgroup_number = IntegerField()
    is_active = BooleanField(default=True)

    class Meta:
        indexes = (
            (('id_group', 'subgroup_number'), True),
        )

    def save(self, *args, **kwargs):
        """Валидация перед сохранением (исправление №2)"""
        if self.id_group <= 0:
            raise ValueError("id_group должен быть больше 0")
        if self.subgroup_number < 1:
            raise ValueError("subgroup_number должен быть больше или равен 1")
        super().save(*args, **kwargs)

    @property
    def name(self) -> str:
        return f"{self.id_group}-{self.subgroup_number}"

    @property
    def count_student(self) -> int:
        return self.students.count()


class Student(BaseModel):
    id_student = IntegerField(unique=True)
    id_subgroup = ForeignKeyField(Subgroup, backref='students', null=True, default=None, on_delete='SET NULL')


def createTables():
    db.create_tables([Subgroup, Student])


if __name__ == '__main__':
    createTables()
    print("Таблицы успешно созданы в БД S8.db")


