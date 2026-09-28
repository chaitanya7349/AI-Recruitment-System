from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobCreate(BaseModel):
    title: str
    description: str
    location: str | None = None
    salary: str | None = None
    experience: str | None = None
    employment_type: str | None = None
    skills: list[str] = []


class JobResponse(BaseModel):
    id: int
    title: str
    description: str
    location: str | None
    salary: str | None
    experience: str | None
    employment_type: str | None
    status: str
    created_at: datetime
    company_name: str

    model_config = ConfigDict(from_attributes=True)
