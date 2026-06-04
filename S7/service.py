from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List
from contextlib import contextmanager
from app.models import Group, Student, db
from datetime import date

app = FastAPI()

# ==================== DATABASE CONNECTION ====================

@contextmanager
def get_db():
    db.connect()
    try:
        yield db
    finally:
        db.close()

# ==================== BUSINESS LOGIC FUNCTIONS ====================

def get_course_number(admission_year: int) -> Optional[int]:
    """Вычисление номера курса"""
    current_date = date.today()
    current_year = current_date.year
    current_month = current_date.month
    
    if current_month >= 9:
        current_academic_year = current_year
    else:
        current_academic_year = current_year - 1
    
    if admission_year > current_academic_year:
        return None
    
    return current_academic_year - admission_year + 1

def get_group_name(group: Group) -> str:
    """Формирование имени группы"""
    course = get_course_number(group.year_create)
    return f"{course}-{group.number}{group.prefix}{group.class_number}"

def get_count_student(group: Group) -> int:
    """Подсчет количества студентов"""
    return group.students.count()

# ==================== SCHEMAS ====================

class CreateGroup(BaseModel):
    year_create: int = Field(..., ge=2000)
    number: int = Field(..., ge=1)
    prefix: str
    code: str = Field(..., pattern=r'^\d{2}\.\d{2}\.\d{2}$')
    class_number: Literal[9, 11]
    tutor_id: Optional[int] = None

class PatchGroup(BaseModel):
    year_create: Optional[int] = Field(None, ge=2000)
    number: Optional[int] = Field(None, ge=1)
    prefix: Optional[str] = None
    code: Optional[str] = Field(None, pattern=r'^\d{2}\.\d{2}\.\d{2}$')
    class_number: Optional[Literal[9, 11]] = None
    tutor_id: Optional[int] = None

class GroupResponse(BaseModel):
    id: int
    year_create: int
    number: int
    prefix: str
    code: str
    class_number: int
    tutor_id: Optional[int] = None
    name: str
    count_student: int
    students: List[int] = []

class GroupShortResponse(BaseModel):
    id: int
    year_create: int

class GroupFilter(BaseModel):
    course_enumeration: Optional[int] = None
    course_minimum_value: Optional[int] = None
    course_maximum_value: Optional[int] = None
    count_student_enumeration: Optional[int] = None
    count_student_minimum_value: Optional[int] = None
    count_student_maximum_value: Optional[int] = None
    prefix: Optional[str] = None
    code: Optional[str] = None
    class_number: Optional[int] = None
    tutor_id: Optional[int] = None

    @field_validator('class_number', mode='before')
    @classmethod
    def validate_class_number(cls, v):
        if v is None:
            return None
        if v not in [9, 11]:
            raise ValueError(f'class_number должен быть 9 или 11, получено: {v}')
        return v

    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        if v is None:
            return None
        import re
        if not re.match(r'^\d{2}\.\d{2}\.\d{2}$', v):
            raise ValueError('code должен быть в формате XX.XX.XX')
        return v

# ==================== CRUD OPERATIONS ====================

def check_unique_combination(db, year_create: int, number: int, prefix: str, class_number: int, exclude_id: Optional[int] = None) -> bool:
    """Проверка уникальности комбинации полей"""
    query = Group.select().where(
        Group.year_create == year_create,
        Group.number == number,
        Group.prefix == prefix,
        Group.class_number == class_number,
        Group.is_active == True
    )
    if exclude_id:
        query = query.where(Group.id != exclude_id)
    return query.exists()

def create_group(db, **data):
    """Создание группы с проверкой уникальности"""
    if check_unique_combination(db, data['year_create'], data['number'], data['prefix'], data['class_number']):
        return None
    
    try:
        return Group.create(**data)
    except IntegrityError:
        return None

def update_group(db, group_id: int, **data):
    """Обновление группы с проверкой уникальности"""
    try:
        group = Group.get_by_id(group_id)
    except DoesNotExist:
        return None
    
    # Проверяем уникальность только если изменяются ключевые поля
    year_create = data.get('year_create', group.year_create)
    number = data.get('number', group.number)
    prefix = data.get('prefix', group.prefix)
    class_number = data.get('class_number', group.class_number)
    
    if check_unique_combination(db, year_create, number, prefix, class_number, group_id):
        return None
    
    for key, value in data.items():
        setattr(group, key, value)
    
    try:
        group.save()
        return group
    except IntegrityError:
        return None

def delete_group(group_id: int):
    """Мягкое удаление группы"""
    try:
        group = Group.get_by_id(group_id)
        group.is_active = False
        group.save()
        return True
    except DoesNotExist:
        return False

def get_group_by_id(group_id: int):
    """Получение группы по ID"""
    try:
        return Group.get_by_id(group_id)
    except DoesNotExist:
        return None

def filter_groups_db(filters: GroupFilter):
    """Фильтрация групп с оптимизацией запросов"""
    # Базовый запрос только активных групп
    query = Group.select().where(Group.is_active == True)
    
    # Применяем фильтры, которые можно выполнить на уровне БД
    if filters.prefix is not None:
        query = query.where(Group.prefix.contains(filters.prefix))
    
    if filters.code is not None:
        query = query.where(Group.code == filters.code)
    
    if filters.class_number is not None:
        query = query.where(Group.class_number == filters.class_number)
    
    if filters.tutor_id is not None:
        query = query.where(Group.tutor_id == filters.tutor_id)
    
    # Получаем группы после базовых фильтров
    groups = list(query)
    
    # Фильтрация по вычисляемым полям (курс)
    if filters.course_enumeration is not None:
        groups = [g for g in groups if get_course_number(g.year_create) == filters.course_enumeration]
    
    if filters.course_minimum_value is not None:
        groups = [g for g in groups if get_course_number(g.year_create) is not None and 
                 get_course_number(g.year_create) >= filters.course_minimum_value]
    
    if filters.course_maximum_value is not None:
        groups = [g for g in groups if get_course_number(g.year_create) is not None and 
                 get_course_number(g.year_create) <= filters.course_maximum_value]
    
    # Фильтрация по количеству студентов (вычисляемое поле)
    if filters.count_student_enumeration is not None:
        groups = [g for g in groups if get_count_student(g) == filters.count_student_enumeration]
    
    if filters.count_student_minimum_value is not None:
        groups = [g for g in groups if get_count_student(g) >= filters.count_student_minimum_value]
    
    if filters.count_student_maximum_value is not None:
        groups = [g for g in groups if get_count_student(g) <= filters.count_student_maximum_value]
    
    return groups

# ==================== API ENDPOINTS ====================

@app.post('/groups', response_model=GroupResponse)
def create_group_endpoint(group: CreateGroup, db=Depends(get_db)):
    """Создание новой группы"""
    try:
        # Бизнес-логика проверки уникальности
        result = create_group(db, **group.model_dump())
        if result is None:
            raise HTTPException(status_code=409, detail="Group with this combination already exists")
        
        return GroupResponse(
            id=result.id,
            year_create=result.year_create,
            number=result.number,
            prefix=result.prefix,
            code=result.code,
            class_number=result.class_number,
            tutor_id=result.tutor_id,
            name=get_group_name(result),
            count_student=get_count_student(result),
            students=[s.id_student for s in result.students]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.patch('/groups/{group_id}', response_model=GroupResponse)
def patch_group_endpoint(group_id: int, group: PatchGroup, db=Depends(get_db)):
    """Частичное обновление группы"""
    update_data = {k: v for k, v in group.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Проверяем существование группы
    existing = get_group_by_id(group_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Бизнес-логика обновления с проверкой уникальности
    result = update_group(db, group_id, **update_data)
    if result is None:
        raise HTTPException(status_code=409, detail="Group with this combination already exists")
    
    return GroupResponse(
        id=result.id,
        year_create=result.year_create,
        number=result.number,
        prefix=result.prefix,
        code=result.code,
        class_number=result.class_number,
        tutor_id=result.tutor_id,
        name=get_group_name(result),
        count_student=get_count_student(result),
        students=[s.id_student for s in result.students]
    )

@app.delete('/groups/{group_id}')
def delete_group_endpoint(group_id: int, db=Depends(get_db)):
    """Мягкое удаление группы"""
    result = delete_group(group_id)
    if not result:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"success": True}

@app.get('/groups/{group_id}', response_model=GroupResponse)
def info_id_endpoint(group_id: int, db=Depends(get_db)):
    """Получение полной информации о группе"""
    result = get_group_by_id(group_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return GroupResponse(
        id=result.id,
        year_create=result.year_create,
        number=result.number,
        prefix=result.prefix,
        code=result.code,
        class_number=result.class_number,
        tutor_id=result.tutor_id,
        name=get_group_name(result),
        count_student=get_count_student(result),
        students=[s.id_student for s in result.students]
    )
    
@app.get('/groups', response_model=List[GroupShortResponse])
def filter_groups_endpoint(
    course_enumeration: Optional[int] = Query(None),
    course_minimum_value: Optional[int] = Query(None),
    course_maximum_value: Optional[int] = Query(None),
    count_student_enumeration: Optional[int] = Query(None),
    count_student_minimum_value: Optional[int] = Query(None),
    count_student_maximum_value: Optional[int] = Query(None),
    prefix: Optional[str] = Query(None),
    code: Optional[str] = Query(None, regex=r'^\d{2}\.\d{2}\.\d{2}$'),
    class_number: Optional[int] = Query(None),
    tutor_id: Optional[int] = Query(None),
    db=Depends(get_db)
):
    """Получение списка групп с фильтрацией"""
    filters = GroupFilter(
        course_enumeration=course_enumeration,
        course_minimum_value=course_minimum_value,
        course_maximum_value=course_maximum_value,
        count_student_enumeration=count_student_enumeration,
        count_student_minimum_value=count_student_minimum_value,
        count_student_maximum_value=count_student_maximum_value,
        prefix=prefix,
        code=code,
        class_number=class_number,
        tutor_id=tutor_id
    )
    
    groups = filter_groups_db(filters)
    return [GroupShortResponse(id=g.id, year_create=g.year_create) for g in groups]
