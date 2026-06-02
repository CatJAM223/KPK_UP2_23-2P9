from app.models.models import Group, Student
from app.schemas import GroupFilter, UpdateGroup
from peewee import *
from datetime import date
import re

def validate_group_data(data: dict) -> tuple[bool, str]:
    if data.get('year_create', 0) < 2000:
        return False, "year_create must be >= 2000"
    if data.get('number', 0) < 1:
        return False, "number must be >= 1"
    if data.get('class_number') not in [9, 11]:
        return False, "class_number must be 9 or 11"
    if data.get('code') and not re.match(r'^\d{2}\.\d{2}\.\d{2}$', data['code']):
        return False, "code must be in format XX.XX.XX"
    return True, ""

def get_course_number(admission_year: int) -> int | None:
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

def create_group(**data):
    try:
        is_valid, error = validate_group_data(data)
        if not is_valid:
            return None
        
        return Group.create(**data)
    except IntegrityError:
        return None

def update_group(group_id: int, update_data: dict):
    try:
        group = Group.get_by_id(group_id)
    except DoesNotExist:
        return None
    
    # Валидация обновляемых полей
    is_valid, error = validate_group_data(update_data)
    if not is_valid:
        return None
    
    # Проверка уникальности при изменении ключевых полей
    if any(field in update_data for field in ['year_create', 'number', 'prefix', 'class_number']):
        new_values = {
            'year_create': update_data.get('year_create', group.year_create),
            'number': update_data.get('number', group.number),
            'prefix': update_data.get('prefix', group.prefix),
            'class_number': update_data.get('class_number', group.class_number),
        }
        exists = Group.select().where(
            (Group.year_create == new_values['year_create']) &
            (Group.number == new_values['number']) &
            (Group.prefix == new_values['prefix']) &
            (Group.class_number == new_values['class_number']) &
            (Group.id != group_id)
        ).exists()
        if exists:
            return None
    
    # Обновление полей
    for key, value in update_data.items():
        setattr(group, key, value)
    
    group.save()
    return group

def delete_group(group_id: int):
    try:
        group = Group.get_by_id(group_id)
    except DoesNotExist:
        return False
    
    return group.soft_delete()

def get_group_info(group_id: int):
    try:
        group = Group.get_by_id(group_id)
    except DoesNotExist:
        return None
    
    # Получение списка студентов
    students = [s.id_student for s in group.students]
    
    return {
        'group': group,
        'students': students,
        'student_count': len(students)
    }

def filter_groups(filters: GroupFilter):
    query = Group.select().where(Group.is_active == True)
    
    # Фильтрация по хранимым полям
    if filters.count_student_enumeration is not None:
        # Примечание: count_student теперь вычисляемое, требует JOIN
        pass
    
    if filters.prefix is not None:
        query = query.where(Group.prefix == filters.prefix)
    
    if filters.code is not None:
        query = query.where(Group.code == filters.code)
    
    if filters.class_number is not None:
        query = query.where(Group.class_number == filters.class_number)
    
    if filters.tutor_id is not None:
        if filters.tutor_id is None or filters.tutor_id == 0:
            query = query.where(Group.tutor_id.is_null(True))
        else:
            query = query.where(Group.tutor_id == filters.tutor_id)
    
    groups = list(query)
    
    if any([filters.course_enumeration, filters.course_minimum_value, filters.course_maximum_value]):
        result = []
        for group in groups:
            course = get_course_number(group.year_create)
            if course is None:
                continue
            
            if filters.course_enumeration is not None and course != filters.course_enumeration:
                continue
            if filters.course_minimum_value is not None and course < filters.course_minimum_value:
                continue
            if filters.course_maximum_value is not None and course > filters.course_maximum_value:
                continue
            result.append(group)
        groups = result
    
    return [{'id': g.id, 'year_create': g.year_create} for g in groups]
