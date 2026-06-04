from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List
from contextlib import contextmanager
from models import Group, Student, db

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
    tutor_id: Optional[int] = 0
    
    
class PatchGroup(BaseModel):
    tutor_id: int

class Groups(BaseModel):
    id: int
    name: str

class BaseSchema(BaseModel):
    year_create: int
    number: int     
    prefix: str  
    code: str = Field(pattern=r'^\d{2}\.\d{2}\.\d{2}$')
    class_number: Literal[9, 11]
    tutor_id: Optional[int] = 0
    name: str            
    count_student: int     
    students: List[int] = []
    
    @classmethod
    def group_to_base(cls, group: Group, group_name: str = None):
        if group_name is None:
            group_name = group.name
    
        return cls(
            year_create=group.year_create,
            number=group.number,
            prefix=group.prefix,
            code=group.code,
            class_number=group.class_number,
            tutor_id=group.tutor_id if group.tutor_id else 0,
            name=group_name,
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
        code: Optional[str] = Query(None, pattern=r'^\d{2}\.\d{2}\.\d{2}$'),
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

def create_group(**data):
    try:
        return Group.create(**data)
    except IntegrityError:
        return None

def delete_group(group_id: int):
    try:
        group = Group.get_by_id(group_id)
    except DoesNotExist:
        return False 
    
    group.is_active = False
    group.save()
    return True

def patch_group(group_id: int, tutor_id: int):
    try:
        group = Group.get_by_id(group_id)
    except DoesNotExist:
        return False
    
    group.tutor_id = tutor_id
    group.save()
    return group, group.name

def info_id(group_id: int):
    try:
        group = Group.get_by_id(group_id)
    except DoesNotExist:
        return False

    return group, group.name

def filter_groups_db(filters: GroupFilter):
    query = Group.select(Group.id, Group.year_create)

    if filters.count_student_enumeration is not None:
        query = query.where(Group.count_student == filters.count_student_enumeration)
    
    if filters.count_student_minimum_value is not None:
        query = query.where(Group.count_student >= filters.count_student_minimum_value)
    
    if filters.count_student_maximum_value is not None:
        query = query.where(Group.count_student <= filters.count_student_maximum_value)
    
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
        result = create_group(**group.dict())
        if result is None:
            raise HTTPException(status_code=409, detail="Group already exists")
        return {"id": result.id, "status": "created"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=str(e))

@app.patch('/groups/{group_id}')
def patch_group_endpoint(group_id: int, group: PatchGroup, db=Depends(get_db)):
    try:
        result = patch_group(group_id, **group.dict())
        if result is False:
            raise HTTPException(404, detail="Group not found")
        
        group_obj, group_name = result
        
        return BaseSchema.group_to_base(group_obj, group_name)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=str(e))

@app.delete('/groups/{group_id}')
def delete_group_endpoint(group_id: int, db=Depends(get_db)):
    try:
        result = delete_group(group_id)
        if not result:
            raise HTTPException(404, detail='Group not found')
        return {"status": "True"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=str(e))

@app.get('/groups/{group_id}')
def info_id_endpoint(group_id: int, db=Depends(get_db)):
    try:
        result = info_id(group_id)
        if result is False:
            raise HTTPException(404, detail="Group not found")
        
        group_obj, group_name = result

        return BaseSchema.group_to_base(group_obj, group_name)
    
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
            "year_created": group.year_create
            }
        for group in query]

        return result
    except HTTPException:
        raise HTTPException(404, detail="Group not found")
    except Exception as e:
        raise HTTPException(400, detail=str(e))
