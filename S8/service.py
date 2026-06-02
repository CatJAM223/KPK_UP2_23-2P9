from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from models import db, Subgroup, Student, createTables

# ==================== Pydantic схемы ====================

class SubgroupCreate(BaseModel):
    id_group: int = Field(..., gt=0, description="ID группы")
    subgroup_number: int = Field(..., ge=1, description="Номер подгруппы")


class SubgroupUpdate(BaseModel):
    id_group: Optional[int] = Field(None, gt=0, description="ID группы")
    subgroup_number: Optional[int] = Field(None, ge=1, description="Номер подгруппы")


class SubgroupResponse(BaseModel):
    id_subgroup: int
    id_group: int
    subgroup_number: int
    name: str
    is_active: bool
    count_student: int


# ==================== FastAPI приложение ====================

app = FastAPI(
    title="Сервис подгрупп",
    description="API для управления подгруппами (вариант №8)",
    version="1.0.0"
)


@app.on_event("startup")
def startup():
    createTables()


@app.post("/subgroups", response_model=SubgroupResponse, status_code=201)
def add_subgroup(subgroup_data: SubgroupCreate):
    """Добавить подгруппу"""
    existing = Subgroup.get_or_none(
        (Subgroup.id_group == subgroup_data.id_group) &
        (Subgroup.subgroup_number == subgroup_data.subgroup_number)
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Подгруппа с таким id_group и subgroup_number уже существует"
        )
    
    subgroup = Subgroup(
        id_group=subgroup_data.id_group,
        subgroup_number=subgroup_data.subgroup_number,
        is_active=True
    )
    subgroup.save()
    
    return SubgroupResponse(
        id_subgroup=subgroup.id_subgroup,
        id_group=subgroup.id_group,
        subgroup_number=subgroup.subgroup_number,
        name=subgroup.name,
        is_active=subgroup.is_active,
        count_student=subgroup.count_student
    )


@app.put("/subgroups/{subgroup_id}", response_model=SubgroupResponse)
def update_subgroup(subgroup_id: int, update_data: SubgroupUpdate):
    """Изменить подгруппу по ID (обновить id_group и/или subgroup_number)"""
    subgroup = Subgroup.get_or_none(Subgroup.id_subgroup == subgroup_id)
    if subgroup is None:
        raise HTTPException(status_code=404, detail="Подгруппа не найдена")
    
    if not subgroup.is_active:
        raise HTTPException(status_code=400, detail="Нельзя изменить закрытую подгруппу")
    
    # Обновляем поля, если они переданы
    if update_data.id_group is not None:
        subgroup.id_group = update_data.id_group
    if update_data.subgroup_number is not None:
        subgroup.subgroup_number = update_data.subgroup_number
    
    # Проверка уникальности после изменения
    existing = Subgroup.get_or_none(
        (Subgroup.id_group == subgroup.id_group) &
        (Subgroup.subgroup_number == subgroup.subgroup_number) &
        (Subgroup.id_subgroup != subgroup_id)
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Подгруппа с таким id_group и subgroup_number уже существует"
        )
    
    subgroup.save()
    
    return SubgroupResponse(
        id_subgroup=subgroup.id_subgroup,
        id_group=subgroup.id_group,
        subgroup_number=subgroup.subgroup_number,
        name=subgroup.name,
        is_active=subgroup.is_active,
        count_student=subgroup.count_student
    )


@app.delete("/subgroups/{subgroup_id}", response_model=bool)
def delete_subgroup(subgroup_id: int):
    """Удалить подгруппу по ID (мягкое удаление)
    
    Возвращает:
    - True - подгруппа была закрыта
    - False - подгруппа уже закрыта или не найдена
    """
    subgroup = Subgroup.get_or_none(Subgroup.id_subgroup == subgroup_id)
    if subgroup is None:
        return False
    
    if not subgroup.is_active:
        return False
    
    subgroup.is_active = False
    subgroup.save()
    return True


@app.get("/subgroups/{subgroup_id}", response_model=SubgroupResponse)
def get_subgroup(subgroup_id: int):
    """Получить подгруппу по ID"""
    subgroup = Subgroup.get_or_none(Subgroup.id_subgroup == subgroup_id)
    if subgroup is None:
        raise HTTPException(status_code=404, detail="Подгруппа не найдена")
    
    return SubgroupResponse(
        id_subgroup=subgroup.id_subgroup,
        id_group=subgroup.id_group,
        subgroup_number=subgroup.subgroup_number,
        name=subgroup.name,
        is_active=subgroup.is_active,
        count_student=subgroup.count_student
    )


@app.get("/subgroups", response_model=List[SubgroupResponse])
def get_subgroups(
    id_group: Optional[int] = Query(None, description="ID группы"),
    subgroup_number: Optional[int] = Query(None, description="Номер подгруппы"),
    name: Optional[str] = Query(None, description="Наименование подгруппы"),
    count_student: Optional[int] = Query(None, description="Количество студентов")
):
    """Получить список подгрупп по заданным параметрам (только активные)"""
    query = Subgroup.select().where(Subgroup.is_active == True)
    
    if id_group is not None:
        query = query.where(Subgroup.id_group == id_group)
    if subgroup_number is not None:
        query = query.where(Subgroup.subgroup_number == subgroup_number)
    
    # Фильтрация по name (на уровне Python, так как name - вычисляемое поле)
    subgroups = list(query)
    
    if name:
        subgroups = [subgroup for subgroup in subgroups if name.lower() in subgroup.name.lower()]
    
    if count_student is not None:
        subgroups = [subgroup for subgroup in subgroups if subgroup.count_student == count_student]
    
    return [
        SubgroupResponse(
            id_subgroup=subgroup.id_subgroup,
            id_group=subgroup.id_group,
            subgroup_number=subgroup.subgroup_number,
            name=subgroup.name,
            is_active=subgroup.is_active,
            count_student=subgroup.count_student
        )
        for subgroup in subgroups
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
