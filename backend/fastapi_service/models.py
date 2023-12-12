# fastapi_service/models.py
from pydantic import BaseModel
from sqlalchemy import Column, String

from databaseTeam4.database import Base


class User(Base):
    __tablename__ = "product_buyers"
    username = Column(String, primary_key=True, index=True)
    firstname = Column(String, index=True)
    lastname = Column(String)
    password = Column(String)
    email_id = Column(String)
    phone_number = Column(String)


class SignupRequest(BaseModel):
    username: str
    # fullname: str
    firstname: str
    lastname: str
    password: str
    email_id: str
    phone_number: str


class SignupResponse(BaseModel):
    username: str
    firstname: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    firstname: str


class TokenData(BaseModel):
    username: str  # Adjusted to use username
