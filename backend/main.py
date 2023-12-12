# fastapi_service/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# from fastapi import FastAPI, HTTPException, status, Depends, APIRouter
# from fastapi_service.models import SignupRequest, SignupResponse, User
# from fastapi_service.oauth2 import get_current_user
# from module.hashing import get_password_hash
# from sqlalchemy import create_engine, text, exc
# from sqlalchemy.orm import Session
from routers import authentication

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(authentication.router)
