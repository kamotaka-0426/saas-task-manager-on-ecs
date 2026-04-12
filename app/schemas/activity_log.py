from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    issue_id: int
    user_id: int
    action: str
    field: str | None
    old_value: str | None
    new_value: str | None
    created_at: datetime
