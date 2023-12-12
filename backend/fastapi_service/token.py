from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi_service import models
import os

# Secret key to encode the JWT token
# SECRET_KEY = os.getenv("SECRET_KEY")
SECRET_KEY = "1cec38d5294ac1c64bade84febff20713811ff50332870fd8140a600e3245d9f"
# Algorithm used to encode the JWT token
ALGORITHM = "HS256"
# Token Expiry time
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = models.TokenData(username=username)
    except JWTError:
        raise credentials_exception
