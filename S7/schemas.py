from pydantic import BaseModel, Field, field_validator
from fastapi import Query
from typing import Optional, Literal, List, Any

class CreateGroup(BaseModel):
    year_create: int = Field(..., ge=2000)
    number: int = Field(..., ge=1)
    prefix: str
    code: str = Field(pattern=r'^\d{2}\.\d{2}\.\d{2}$')
    class_number: Literal[9, 11]
    tutor_id: Optional[int] = None

class UpdateGroup(BaseModel):
    """Схема для обновления группы (все поля необязательные)"""
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
    
    @classmethod
    def from_group_with_students(cls, group, students: List[int]):
        return cls(
            id=group.id,
            year_create=group.year_create,
            number=group.number,
            prefix=group.prefix,
            code=group.code,
            class_number=group.class_number,
            tutor_id=group.tutor_id,
            name=group.name,
            count_student=len(students),
            students=students
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
