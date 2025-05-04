from pydantic import BaseModel
from enum import Enum

class UserRole(str, Enum):
    GAMER = "gamer"
    CLAN_CHIEF = "clan_chief"

class User(BaseModel):
    username: str
    role: UserRole

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str
    role: UserRole 