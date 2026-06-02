from app.models.models import Group
from app.schemas import GroupFilter
from peewee import * 

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
    
    if not group.is_active:
        return False
    
    group.is_active = False
    group.save()
    return True

def patch_group(group_id: int, tutor_id: int):
    try:
        group = Group.get_by_id(group_id)
    except DoesNotExist:
        return None
    
    group.tutor_id = tutor_id
    group.save()
    return group

def info_id(group_id: int):
    try:
        group = Group.get_by_id(group_id)
    except DoesNotExist:
        return None

    return group

def filter_groups(filters: GroupFilter):
    query = Group.select(Group.id, Group.year_create).where(Group.is_active == True)

    if filters.count_student_enumeration is not None:
        query = query.where(Group.count_student == filters.count_student_enumeration)
    
    if filters.count_student_minimum_value is not None:
        query = query.where(Group.count_student >= filters.count_student_minimum_value)
    
    if filters.count_student_maximum_value is not None:
        query = query.where(Group.count_student <= filters.count_student_maximum_value)
    
    if filters.prefix is not None:
        query = query.where(Group.prefix == filters.prefix)
    
    if filters.code is not None:
        query = query.where(Group.code == filters.code)
    
    if filters.class_number is not None:
        query = query.where(Group.class_number == filters.class_number)
    
    if filters.tutor_id is not None:
        # Преобразуем 0 в None для поиска NULL
        if filters.tutor_id == 0:
            query = query.where(Group.tutor_id.is_null(True))
        else:
            query = query.where(Group.tutor_id == filters.tutor_id)

    groups = list(query)
    
    if filters.course_enumeration is not None:
        groups = [g for g in groups if Group.get_course_number(g.year_create) == filters.course_enumeration]
    
    if filters.course_minimum_value is not None:
        groups = [g for g in groups if Group.get_course_number(g.year_create) is not None 
                  and Group.get_course_number(g.year_create) >= filters.course_minimum_value]
    
    if filters.course_maximum_value is not None:
        groups = [g for g in groups if Group.get_course_number(g.year_create) is not None 
                  and Group.get_course_number(g.year_create) <= filters.course_maximum_value]

    return groups