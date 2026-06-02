from typing import Annotated
from fastapi import Depends, HTTPException, APIRouter, Request, Query
from peewee import DoesNotExist
from models import Permission
from logic import check_permission
from pydantic_models import EditPermission
import requests


async def require_permission(request: Request):
    """
    Когда будет сделан jwt токен то вместо 'role_id = 1'
    надо указать следующее:
    1) Получить токен из заголовка
       token = request.headers.get('Authorization')
    2) Дальше декодировать токен
       payload = функция_для_декодирования_или_сервис(token)
    3) Дальше передать параметр
       role_id = payload['role_id']
    КРИТИЧЕСКИ ВАЖНО!!!
    Здесь role_id - ЗАГЛУШКА
    """
    role_id = requests.get('http://127.0.0.1:5000/users/info/me/').json()

    answer = await check_permission(role_id = role_id, method = str(request.method), url = str(request.url.path))
    if answer["status_code"] == 200:
        answer.pop("status_code")
        return answer
    else:
        answer.pop("status_code")
        raise HTTPException(status_code=403, detail=answer)

router = APIRouter(prefix='/permissions',tags=["Permission"], dependencies=[Depends(require_permission)])

@router.get('/')
async def get_permissions(
        permission_id: Annotated[int, Query(...,ge=1)] = None,
        role_id: Annotated[int, Query(...,ge=1,le=6)] = None,
        limit: Annotated[int, Query(...,ge=0,le=100)] = None,
        offset: Annotated[int, Query(...,ge=0)] = None,
):
    if role_id:
        answer = []
        for p in Permission.select().limit(limit).offset(offset).where(Permission.role_id == role_id):
            answer.append({'permission_id':p.id,'method': p.method, 'url': p.url})
        return answer
    if permission_id:
        try:
            permission = Permission.get_by_id(permission_id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Разрешение не найдено")

        return {
            "permission_id": permission.id,
            "role_id": permission.role_id,
            "method": permission.method,
            "url": permission.url
        }
    answer = {
        1: [],
        2: [],
        3: [],
        4: [],
        5: [],
        6: []
    }
    for p in Permission.select().offset(offset).limit(limit):
        if p.role_id in answer:
            answer[p.role_id].append({'permission_id':p.id,'method':p.method, 'url':p.url})
    return answer

@router.post('/{role_id}/')
async def create_permission(role_id: int, method: str, url: str):

    existing = Permission.select().where(
        (Permission.role_id == role_id) &
        (Permission.method == method.upper()) &
        (Permission.url == url)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Такое разрешение уже существует")

    permission = Permission.create(
        role_id=role_id,
        method=method,
        url=url
    )

    return {
        "status_code": 201,
        "detail": "Привилегия создана",
        "permission_id": permission.id
    }

@router.patch('/{permission_id}/')
async def update_permission(permission_id: int,permission_data: EditPermission):
    try:
        Permission.get_by_id(permission_id)
    except DoesNotExist:
        raise HTTPException(status_code=404,detail='Запись не найдена')

    update_data = permission_data.model_dump(exclude_unset=True)

    try:
        Permission.update(update_data).where(Permission.id == permission_id).execute()
    except:
        raise HTTPException(status_code=400, detail='Ошибка в названии метода')
    return {
        "status_code": 200,
        "detail": "Запись обновлена",
        "permission_id": permission_id
    }

@router.delete('/{permission_id}/')
async def delete_permission(permission_id: int):
    try:
        permission = Permission.get_by_id(permission_id)
    except DoesNotExist:
        raise HTTPException(status_code=404,detail='Запись не найдена')
    permission.delete_instance()
    return {
        "status_code": 200,
        "detail": "Запись удалена",
        "permission_id": permission_id
    }