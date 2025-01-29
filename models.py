from pydantic import ConfigDict, BaseModel, Field, EmailStr
from typing import Optional

class UserModel(BaseModel):
    name: str
    email: str
    password: str
    
    model_config = ConfigDict(
        populate_by_names=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "name": "John Doe",
                "email": "johndoes@example.com",
                "password": "passwordhashexample"
            }
        },
        from_attributes=True,
    )
    

class UpdateUserModel(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        # json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "name": "John Doe",
                "email": "johndoes@example.com",
                "password": "passwordhashexample"
                }
        },
        from_attributes=True,
    )


class UserLoginModel(BaseModel):
    email: EmailStr
    password: str
    

class SbirRequest(BaseModel):
    user_id: str
    date_from: str
    date_to: str
    rate: bool

class SamRequest(BaseModel):
    user_id: str
    rate: bool
    
    
class DomainsRequest(BaseModel):
    user_id: str
    platform: str