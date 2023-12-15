from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from databaseTeam4.database import get_db
from fastapi_service.models import User
from fastapi_service.token import create_access_token
from module.hashing import get_password_hash, verify_password
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Depends
from fastapi_service.models import SignupRequest, SignupResponse
from sqlalchemy import create_engine, text, exc

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from databaseTeam4.database import get_db
from fastapi_service.models import User
from fastapi_service.token import create_access_token
from module.hashing import get_password_hash, verify_password
from sqlalchemy.orm import Session


from fastapi import FastAPI, HTTPException, status, Depends
from fastapi_service.models import SignupRequest, SignupResponse
from module.hashing import get_password_hash
from sqlalchemy import create_engine, text, exc
from sqlalchemy.orm import Session
from fastapi_service.oauth2 import get_current_user
import os

# DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)


def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()


router = APIRouter(tags=["Authentication"])


@router.post("/signup", response_model=SignupResponse)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    hashed_password = get_password_hash(request.password)
    query = text(
        "INSERT INTO product_buyers (username, firstname, lastname, email_id, phone_number, password) VALUES (:username, :firstname, :lastname ,:email_id,:phone_number, :password)"
    )
    values = {
        "username": request.username,
        "firstname": request.firstname,
        "lastname": request.lastname,
        "email_id": request.email_id,
        "phone_number": request.phone_number,
        "password": hashed_password,
    }
    try:
        # Start a new transaction
        db.begin()
        db.execute(query, values)  # Execute the custom INSERT statement
        db.commit()
        return {"username": request.username, "firstname": request.firstname}
    except exc.SQLAlchemyError as e:  # Catch any SQLAlchemy errors
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login")
def login(
    request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Credentials"
        )
    if not verify_password(request.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Incorrect password"
        )

    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "firstname": user.firstname,
    }
