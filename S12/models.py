from peewee import *
from datetime import datetime

db = SqliteDatabase('curriculum.db')


class BaseModel(Model):
    class Meta:
        database = db


class AssessmentForm:
    """Формы отчетности (Enum)"""
    EXAM = 'exam'
    CREDIT = 'credit'
    CHOICES = [EXAM, CREDIT]


class Group(BaseModel):
    """Группа студентов"""
    id = AutoField(primary_key=True)
    name = CharField(max_length=100, unique=True, null=False)

    class Meta:
        table_name = 'groups'


class Discipline(BaseModel):
    """Дисциплина"""
    id = AutoField(primary_key=True)
    name = CharField(max_length=200, unique=True, null=False)

    class Meta:
        table_name = 'disciplines'


class Semester(BaseModel):
    """Семестр"""
    id = AutoField(primary_key=True)
    semester_number = IntegerField(null=False, constraints=[Check('semester_number BETWEEN 1 AND 8')])
    academic_year = CharField(max_length=9, null=False)

    class Meta:
        table_name = 'semesters'
        constraints = [SQL('UNIQUE(semester_number, academic_year)')]


class Curriculum(BaseModel):
    id = AutoField(primary_key=True)

    # Внешние ключи (NOT NULL)
    group = ForeignKeyField(Group, backref='curriculums', on_delete='CASCADE', null=False)
    discipline = ForeignKeyField(Discipline, backref='curriculums', on_delete='CASCADE', null=False)
    semester = ForeignKeyField(Semester, backref='curriculums', on_delete='RESTRICT', null=False)

    # Поля с ограничениями (NOT NULL, без default)
    theory_hours = IntegerField(
        null=False,
        constraints=[Check('theory_hours >= 0')]
    )
    practice_hours = IntegerField(
        null=False,
        constraints=[Check('practice_hours >= 0')]
    )
    assessment_form = CharField(
        max_length=10,
        null=False,
        constraints=[Check("assessment_form IN ('exam', 'credit')")]
    )

    # Мягкое удаление
    is_active = BooleanField(default=True, null=False)

    class Meta:
        table_name = 'curriculum'
        constraints = [
            SQL('UNIQUE(group_id, discipline_id, semester_id)')
        ]
        indexes = (
            (('group_id',), False),
            (('discipline_id',), False),
            (('semester_id',), False),
            (('is_active',), False),
        )

    @classmethod
    def _validate_required_fields(cls, **kwargs):
        required_fields = ['group', 'discipline', 'semester', 
                          'theory_hours', 'practice_hours', 'assessment_form']
        missing = [f for f in required_fields if f not in kwargs or kwargs[f] is None]
        if missing:
            raise ValueError(f"Отсутствуют обязательные поля: {', '.join(missing)}")

    @classmethod
    def _validate_hours(cls, theory_hours, practice_hours):
        if theory_hours < 0:
            raise ValueError(f"theory_hours должно быть >= 0, получено {theory_hours}")
        if practice_hours < 0:
            raise ValueError(f"practice_hours должно быть >= 0, получено {practice_hours}")

    @classmethod
    def _validate_assessment_form(cls, assessment_form):
        if assessment_form not in AssessmentForm.CHOICES:
            raise ValueError(f"assessment_form должно быть 'exam' или 'credit', получено {assessment_form}")

    def to_dict(self):
        return {
            'id': self.id,
            'discipline_id': self.discipline.id,
            'discipline_name': self.discipline.name,
            'group_id': self.group.id,
            'group_name': self.group.name,
            'semester_id': self.semester.id,
            'semester_number': self.semester.semester_number,
            'semester_academic_year': self.semester.academic_year,
            'theory_hours': self.theory_hours,
            'practice_hours': self.practice_hours,
            'assessment_form': self.assessment_form,
            'is_active': self.is_active
        }

    @classmethod
    def create_curriculum(cls, group, discipline, semester, theory_hours, practice_hours, assessment_form):
        cls._validate_required_fields(
            group=group, discipline=discipline, semester=semester,
            theory_hours=theory_hours, practice_hours=practice_hours,
            assessment_form=assessment_form
        )

        cls._validate_hours(theory_hours, practice_hours)
        cls._validate_assessment_form(assessment_form)

        record = cls.create(
            group=group,
            discipline=discipline,
            semester=semester,
            theory_hours=theory_hours,
            practice_hours=practice_hours,
            assessment_form=assessment_form
        )

        return record.to_dict()

    @classmethod
    def get_by_id_with_names(cls, record_id):
        try:
            record = cls.get_by_id(record_id)
            return record.to_dict()
        except DoesNotExist:
            return None

    def soft_delete(self):
        if not self.is_active:
            return False
        self.is_active = False
        self.save()
        return True

    def update_fields(self, **kwargs):
        # Запрещённые поля
        forbidden_fields = ['group', 'group_id', 'discipline', 'discipline_id', 
                           'semester', 'semester_id', 'id', 'is_active']

        for field in forbidden_fields:
            if field in kwargs:
                raise ValueError(f"Поле '{field}' нельзя изменить после создания")

        if 'theory_hours' in kwargs or 'practice_hours' in kwargs:
            theory = kwargs.get('theory_hours', self.theory_hours)
            practice = kwargs.get('practice_hours', self.practice_hours)
            self._validate_hours(theory, practice)

        if 'assessment_form' in kwargs:
            self._validate_assessment_form(kwargs['assessment_form'])

        allowed_fields = ['theory_hours', 'practice_hours', 'assessment_form']

        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(self, key, value)

        self.save()
        return self.to_dict()

    @classmethod
    def get_filtered_list(cls, filters=None, page=1, page_size=20):
        query = cls.select()

        if filters is None:
            filters = {}

        apply_default_active = 'is_active' not in filters or filters['is_active'] is None
        if apply_default_active:
            query = query.where(cls.is_active == True)

        if filters.get('group_id') is not None:
            query = query.where(cls.group_id == filters['group_id'])
        if filters.get('discipline_id') is not None:
            query = query.where(cls.discipline_id == filters['discipline_id'])
        if filters.get('semester_id') is not None:
            query = query.where(cls.semester_id == filters['semester_id'])
        if filters.get('semester_number') is not None:
            query = query.where(cls.semester_id << Semester.select(Semester.id).where(
                Semester.semester_number == filters['semester_number']))
        if filters.get('assessment_form') is not None:
            query = query.where(cls.assessment_form == filters['assessment_form'])

        # Диапазоны часов
        if filters.get('theory_hours_min') is not None:
            query = query.where(cls.theory_hours >= filters['theory_hours_min'])
        if filters.get('theory_hours_max') is not None:
            query = query.where(cls.theory_hours <= filters['theory_hours_max'])
        if filters.get('practice_hours_min') is not None:
            query = query.where(cls.practice_hours >= filters['practice_hours_min'])
        if filters.get('practice_hours_max') is not None:
            query = query.where(cls.practice_hours <= filters['practice_hours_max'])

        if 'is_active' in filters and filters['is_active'] is not None:
            query = query.where(cls.is_active == filters['is_active'])

        query = query.order_by(cls.id)

        total = query.count()

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        items = [record.to_dict() for record in query]

        return {
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size if total > 0 else 0
        }

def create_tables():
    db.connect()
    db.create_tables([Group, Discipline, Semester, Curriculum], safe=True)
    db.close()


def add_default_data():
    if Semester.select().count() == 0:
        for year in range(2024, 2026):
            for sem in range(1, 5):
                Semester.create(semester_number=sem, academic_year=f"{year}-{year+1}")
        print("✓ Семестры добавлены")


if __name__ == "__main__":
    create_tables()
    add_default_data()
    print("База данных и таблицы созданы успешно!")
