from pydantic import BaseModel, EmailStr


class EmployerRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

    company_name: str
    company_description: str | None = None
    company_website: str | None = None
    company_location: str | None = None

    designation: str | None = None
    role_in_company: str | None = None
