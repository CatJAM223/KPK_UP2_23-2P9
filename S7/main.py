from fastapi import FastAPI, Depends, HTTPException, Query
from app.schemas import CreateGroup, PatchGroup, Base, Groups, GroupFilter
from app.database import get_db
from app.crud import (
create_group as create_db,
patch_group as patch_db,
delete_group as delete_db,
info_id as info_id_db,
filter_groups as filter_groups_db,
)

app = FastAPI()

@app.post('/groups')
def create_group(group: CreateGroup, db=Depends(get_db)):
    try:
        result = create_db(**group.dict())
        if result is None:
            raise HTTPException(status_code=409, detail="Group already exists")
        return {"id": result.id, "status": "created"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=str(e))

@app.patch('/groups/{group_id}')
def patch_group(group_id: int, group: PatchGroup, db=Depends(get_db)):
    try:
        result = patch_db(group_id, **group.dict())
        if result is False:
            raise HTTPException(404, detail="Group not found")
        
        group, group_name = result
        
        return Base.group_to_base(group, group_name)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=e)

@app.delete('/groups/{group_id}')
def delete_group(group_id: int, db=Depends(get_db)):
    try:
        result = delete_db(group_id)
        if not result:
            raise HTTPException(404, detail='Group not found')
        return {"status": "True"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=str(e))

@app.get('/groups/{group_id}')
def info_id(group_id: int, db=Depends(get_db)):
    try:
        result = info_id_db(group_id)
        if result is False:
            raise HTTPException(404, detail="Group not found")
        
        group, group_name = result

        return Base.group_to_base(group, group_name)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=e)
    
@app.get('/groups')
def filter_groups(filters: GroupFilter = Depends(GroupFilter.query_params), db=Depends(get_db)):
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