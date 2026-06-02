from pydantic import BaseModel, Field
from typing import Optional, Annotated

class EditPermission(BaseModel):
    role_id: Annotated[int, Field(ge=1,le=6)] = None
    method: Annotated[str,Field(
        pattern=r'^(GET|HEAD|OPTIONS|POST|PUT|PATCH|TRACE|CONNECT|DELETE)$'
    )] = None
    url: Optional[str] = None