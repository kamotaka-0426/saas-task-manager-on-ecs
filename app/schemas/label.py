from pydantic import BaseModel, ConfigDict, Field


class LabelCreate(BaseModel):
    name: str
    color: str = Field(default="#6366f1", pattern=r"^#[0-9a-fA-F]{6}$")


class LabelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    org_id: int
    name: str
    color: str
