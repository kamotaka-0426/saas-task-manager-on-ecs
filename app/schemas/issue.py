from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.issue import StatusEnum, PriorityEnum
from app.schemas.label import LabelResponse
from app.schemas.comment import CommentResponse
from app.schemas.activity_log import ActivityLogResponse


class UserMini(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str


class IssueCreate(BaseModel):
    title: str
    description: str | None = None
    status: StatusEnum = StatusEnum.backlog
    priority: PriorityEnum = PriorityEnum.none


class IssueUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: StatusEnum | None = None
    priority: PriorityEnum | None = None


class IssueResponse(BaseModel):
    """Returned in list endpoints — includes assignees/labels but not comments."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    description: str | None
    status: StatusEnum
    priority: PriorityEnum
    created_by: int
    created_at: datetime
    updated_at: datetime
    assignees: list[UserMini] = []
    labels: list[LabelResponse] = []


class IssueDetailResponse(IssueResponse):
    """Returned in single-issue GET — includes full comments and activity log."""
    comments: list[CommentResponse] = []
    activity_logs: list[ActivityLogResponse] = []


class PaginatedIssues(BaseModel):
    items: list[IssueResponse]
    next_cursor: str | None
    total: int
