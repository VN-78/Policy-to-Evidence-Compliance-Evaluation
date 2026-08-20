from pydantic import BaseModel, EmailStr


# What we expect FROM the user
class UserCreate(BaseModel):
    username: str
    email: EmailStr

# What we send BACK to the user
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
