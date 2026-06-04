from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List
from contextlib import contextmanager
from app.models import Group, Student, db

# ==================== DATABASE CONNECTION ====================

@contextmanager
def get_db():
    db.connect()
    try:
        yield db
    finally:
        db.close()

# ==================== SCHEMAS ====================

class CreateGroup(BaseModel):
    year_create: int = Field(..., ge=2000)
    number: int = Field(..., ge=1)
    prefix: str
    code: str = Field(pattern=r'^\d{2}\.\d{2}\.\d{2}$')
    class_number: Literal[9, 11]
    tutor_id: Optional[int] = None  # Изменено с 0 на None

class PatchGroup(BaseModel):
    year_create: Optional[int] = Field(None, ge=2000)
    number: Optional[int] = Field(None, ge=1)
    prefix: Optional[str] = None
    code: Optional[str] = Field(None, pattern=r'^\d{2}\.\d{2}\.\d{2}$')
    class_number: Optional[Literal[9, 11]] = None
    tutor_id: Optional[int] = None

class BaseSchema(BaseModel):
    year_create: int
    number: int     
    prefix: str  
    code: str = Field(pattern=r'^\d{2}\.\d{2}\.\d{2}$')
    class_number: Literal[9, 11]
    tutor_id: Optional[int] = None  # Изменено с 0 на None
    name: str            
    count_student: int     
    students: List[int] = []
    
    @classmethod
    def group_to_base(cls, group: Group):
        return cls(
            year_create=group.year_create,
            number=group.number,
            prefix=group.prefix,
            code=group.code,
            class_number=group.class_number,
            tutor_id=group.tutor_id,
            name=group.name,
            count_student=group.count_student,
            students=[s.id_student for s in group.students]
        )   
    
class GroupFilter(BaseModel):
    course_enumeration: Optional[int] = None
    course_minimum_value: Optional[int] = None
    course_maximum_value: Optional[int] = None
    count_student_enumeration: Optional[int] = None
    count_student_minimum_value: Optional[int] = None
    count_student_maximum_value: Optional[int] = None
    prefix: Optional[str] = None
    code: Optional[str] = Field(None, pattern=r'^\d{2}\.\d{2}\.\d{2}$')
    class_number: Optional[int] = None
    tutor_id: Optional[int] = None

    @field_validator('class_number', mode='before')
    @classmethod
    def validate_class_number(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                v = int(v)
            except ValueError:
                raise ValueError('class_number должен быть числом')
        if v not in [9, 11]:
            raise ValueError(f'class_number должен быть 9 или 11, получено: {v}')
        return v

    @classmethod
    def query_params(
        cls,
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
    ):
        return cls(
            course_enumeration=course_enumeration,
            course_minimum_value=course_minimum_value,
            course_maximum_value=course_maximum_value,
            count_student_enumeration=count_student_enumeration,
            count_student_minimum_value=count_student_minimum_value,
            count_student_maximum_value=count_student_maximum_value,
            prefix=prefix,
            code=code,
            class_number=class_number,
            tutor_id=tutor_id,
        )

# ==================== CRUD OPERATIONS ====================

def check_unique_combination(year_create, number, prefix, class_number, exclude_id=None):
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

def create_group(**data):
    # Проверка уникальности
    if check_unique_combination(
        data['year_create'], 
        data['number'], 
        data['prefix'], 
        data['class_number']
    ):
        return None
    
    try:
        return Group.create(**data)
    except IntegrityError:
        return None

def update_group(group_id: int, **data):
    try:
        group = Group.get_by_id(group_id)
    except DoesNotExist:
        return None
    
    # Проверка уникальности при изменении
    new_year_create = data.get('year_create', group.year_create)
    new_number = data.get('number', group.number)
    new_prefix = data.get('prefix', group.prefix)
    new_class_number = data.get('class_number', group.class_number)
    
    if check_unique_combination(new_year_create, new_number, new_prefix, new_class_number, group_id):
        return None
    
    for key, value in data.items():
        setattr(group, key, value)
    
    group.save()
    return group

def delete_group(group_id: int):
    try:
        group = Group.get_by_id(group_id)
    except DoesNotExist:
        return False 
    
    group.is_active = False
    group.save()
    return True

def info_id(group_id: int):
    try:
        group = Group.get_by_id(group_id)
    except DoesNotExist:
        return None

    return group

def filter_groups_db(filters: GroupFilter):
    # Только активные группы
    query = Group.select().where(Group.is_active == True)

    if filters.count_student_enumeration is not None:
        # Фильтрация по вычисляемому полю требует подзапроса или фильтрации после выборки
        groups = list(query)
        groups = [g for g in groups if g.count_student == filters.count_student_enumeration]
        query = groups
        return query if isinstance(query, list) else list(query)
    
    if filters.count_student_minimum_value is not None:
        groups = list(query) if not isinstance(query, list) else query
        groups = [g for g in groups if g.count_student >= filters.count_student_minimum_value]
        query = groups
    
    if filters.count_student_maximum_value is not None:
        groups = list(query) if not isinstance(query, list) else query
        groups = [g for g in groups if g.count_student <= filters.count_student_maximum_value]
        query = groups
    
    if filters.prefix is not None:
        query = query.where(Group.prefix.contains(filters.prefix))
    
    if filters.code is not None:
        query = query.where(Group.code == filters.code)
    
    if filters.class_number is not None:
        query = query.where(Group.class_number == filters.class_number)
    
    if filters.tutor_id is not None:
        query = query.where(Group.tutor_id == filters.tutor_id)

    groups = list(query)
    
    if filters.course_enumeration is not None:
        groups = [g for g in groups if Group.get_course_number(g.year_create) == filters.course_enumeration]
    
    if filters.course_minimum_value is not None:
        groups = [g for g in groups if Group.get_course_number(g.year_create) is not None and Group.get_course_number(g.year_create) >= filters.course_minimum_value]
    
    if filters.course_maximum_value is not None:
        groups = [g for g in groups if Group.get_course_number(g.year_create) is not None and Group.get_course_number(g.year_create) <= filters.course_maximum_value]

    return groups

# ==================== FASTAPI APP ====================

app = FastAPI()

@app.post('/groups')
def create_group_endpoint(group: CreateGroup, db=Depends(get_db)):
    try:
        result = create_group(**group.model_dump())
        if result is None:
            raise HTTPException(status_code=409, detail="Group already exists")
        
        # Возвращаем созданный объект полностью
        return BaseSchema.group_to_base(result)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=str(e))

@app.patch('/groups/{group_id}')
def patch_group_endpoint(group_id: int, group: PatchGroup, db=Depends(get_db)):
    try:
        # Убираем None значения
        update_data = {k: v for k, v in group.model_dump().items() if v is not None}
        
        if not update_data:
            raise HTTPException(400, detail="No fields to update")
        
        result = update_group(group_id, **update_data)
        if result is None:
            # Проверяем, существует ли группа
            existing = info_id(group_id)
            if existing is None:
                raise HTTPException(404, detail="Group not found")
            else:
                raise HTTPException(409, detail="Group with this combination already exists")
        
        return BaseSchema.group_to_base(result)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=str(e))

@app.delete('/groups/{group_id}')
def delete_group_endpoint(group_id: int, db=Depends(get_db)):
    try:
        result = delete_group(group_id)
        if not result:
            return {"success": False}
        return {"success": True}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=str(e))

@app.get('/groups/{group_id}')
def info_id_endpoint(group_id: int, db=Depends(get_db)):
    try:
        result = info_id(group_id)
        if result is None:
            raise HTTPException(404, detail="Group not found")

        return BaseSchema.group_to_base(result)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=str(e))
    
@app.get('/groups')
def filter_groups_endpoint(filters: GroupFilter = Depends(GroupFilter.query_params), db=Depends(get_db)):
    try:
        query = filter_groups_db(filters)
        result = [{
            "id": group.id,
            "year_create": group.year_create  # Исправлено с year_created на year_create
            }
        for group in query]

        return result
    except HTTPException:
        raise HTTPException(404, detail="Group not found")
    except Exception as e:
        raise HTTPException(400, detail=str(e))

# ==================== RUN SERVER ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
