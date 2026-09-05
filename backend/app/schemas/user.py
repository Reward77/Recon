from pydantic import BaseModel
from pydantic import EmailStr


class RegisterUser(BaseModel):

    company_name: str

    full_name: str

    email: EmailStr

    password: str


class LoginUser(BaseModel):

    email: EmailStr

    password: str


class CreateUserRequest(BaseModel):

    full_name: str

    email: EmailStr

    password: str

    role: str


class UserResponse(BaseModel):

    id: str

    full_name: str

    email: EmailStr

    role: str

    is_active: bool

    class Config:
        from_attributes = True