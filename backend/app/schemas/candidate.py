from pydantic import BaseModel, EmailStr


class CandidateRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class CandidateProfileCreate(BaseModel):
    phone: str | None = None
    location: str | None = None
    bio: str | None = None
    experience: str | None = None
    education: str | None = None


class ApplicationCreate(BaseModel):
    job_id: int
    resume_id: int | None = None
