import os
import secrets
import pytz
from fastapi import Depends, FastAPI, HTTPException, status, Request, Response, Body
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Annotated
from app.db.database import get_db
from app.models import User, RefreshToken, Role
import logging
import jwt
from app.crypto import hash_password_bcrypt,hash_password_pbkdf2,verify_password_bcrypt,verify_password_pbkdf2
from datetime import datetime, timedelta, timezone
from jwt.exceptions import InvalidTokenError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.dependencies import oauth2_scheme
from jwt import  decode
from jose import JWTError
from typing import Optional







logger = logging.getLogger(__name__)
router = APIRouter()
SECRET_KEY = os.getenv("SECRET_KEY", "0456dffffhtghbvnughjghfg5dfgd57hgbnmbx3e7")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 1))
print(f"ACCESS_TOKEN_EXPIRE_MINUTES from env: {access_token_expire_minutes}")
class UserData(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    middle_name: str | None = None
    password: str
    password_confirm: str


class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None


#generate refresh token
def create_refresh_token():
    return secrets.token_hex(32)

#generate jwt token with expire time
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    current_utc = datetime.now(pytz.utc)
    current_local = datetime.now()

    print(f"Current UTC: {current_utc}")
    print(f"Current local: {current_local}")

    to_encode = data.copy()
    if expires_delta:
        expire = current_utc + expires_delta
    else:
        expire = current_utc + timedelta(minutes=access_token_expire_minutes)

    print(f"Token will expire at UTC: {expire}")
    print(f"Token will expire at local: {expire.astimezone(pytz.timezone('Asia/Yekaterinburg'))}")  # для +5

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

#check time and token
def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": True})
        print(f"Decoded JWT payload: {payload}")


        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            exp_time_utc = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            exp_time_local = datetime.fromtimestamp(exp_timestamp)
            current_utc = datetime.now(pytz.utc)
            current_local = datetime.now()

            print(f"Token expiry UTC: {exp_time_utc}")
            print(f"Token expiry local: {exp_time_local}")
            print(f"Current UTC: {current_utc}")
            print(f"Current local: {current_local}")
            print(f"Token expired: {current_utc > exp_time_utc}")

        return payload
    except jwt.ExpiredSignatureError:
        print("❌ Token has expired!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except JWTError as e:
        print(f"❌ JWT Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )



#get user from token
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    logger.debug(f"Received token: {token}")
    try:

        payload = decode_access_token(token)
        username = payload.get("sub")  # sub

        logger.debug(f"Decoded payload: {payload}")
        if username is None:
            logger.error("Username is None in the token.")
            raise credentials_exception

        token_data = TokenData(username=username)

    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
        )


    logger.debug(f"User found: {user.username}")

    if "iat" in payload:
        token_issue_time = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        logger.debug(f"Token issued at (UTC): {token_issue_time}")

    return user



def get_current_active_user(request: Request,db: Session = Depends(get_db)) -> User:
    pass


# login + give JWT-token to user , passw data
@router.post("/token")
async def login_for_access_token(response: Response,form_data: Annotated[OAuth2PasswordRequestForm, Depends()],db: Session = Depends(get_db)) -> Token:
    user = db.query(User).filter(User.username == form_data.username).first()
    print(f"token user {user}")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password_bcrypt(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token()
    refresh_token_expires = datetime.now(tz=pytz.utc) + timedelta(days=refresh_token_expire_days)  #datetime.utcnow()
#

    #token_print = Token(access_token=access_token, token_type="bearer")
    print(f"access_token {access_token}")
    print(f"refresh_token {refresh_token}")
    # db refresh token save
    db_refresh = RefreshToken(user_id=user.id, token=refresh_token, expires_at=refresh_token_expires)
    db.add(db_refresh)
    db.commit()
    #User.disabled = False

    #response.set_cookie(
    #    key="refresh_token",
    #    value=refresh_token,
    #    httponly=True,
    #    secure=True,
    #    samesite="Strict",
    #    expires=int(refresh_token_expires.timestamp())
    #)


    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh")
async def refresh_access_token(refresh_data: dict, db: Session = Depends(get_db)):
    print(f"REFRESH endpoint:")
    #refresh_token = request.cookies.get("refresh_token")
    refresh_token = refresh_data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token required")
    try:
        db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
        print(f"RefreshToken.token:{RefreshToken.token},refresh_token:{refresh_token}")
        print(f"db_token.expires_at:{db_token.expires_at},datetime.now(pytz.utc):{datetime.now(pytz.utc)} ")
        if not db_token:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        current_utc = datetime.now(pytz.utc)
        current_local = datetime.now()

        print(f"DB token expires at: {db_token.expires_at}")
        print(f"Current UTC: {current_utc}")
        print(f"Current local: {current_local}")
        print(f"Refresh token expired: {current_utc > db_token.expires_at}")



        if db_token.expires_at < datetime.now(pytz.utc):
            raise HTTPException(status_code=401, detail="Refresh token has expired")

        user = db.query(User).filter(User.id == db_token.user_id).first()

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        # new access token
        access_token_expires = timedelta(minutes=access_token_expire_minutes)
        access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
        print(f"new access:{access_token}")
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


class LogoutRequest(BaseModel):
    refresh_token: str


@router.post("/logout")
async def logout(
        logout_request: LogoutRequest,
        db: Session = Depends(get_db)
):
    refresh_token = logout_request.refresh_token

    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token required")


    db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if db_token:
        db.delete(db_token)
        db.commit()
        return {"message": "Logged out successfully"}
    else:
        return {"message": "Logged out successfully"}



#register user
@router.post("/register")
def register(user_data: UserData, db: Session = Depends(get_db)):
    logger.info("/register endpoint - Attempt to register user: %s", user_data.username)
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")


    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")


    if user_data.password != user_data.password_confirm:
        raise HTTPException(status_code=400, detail="Passwords do not match")


    if len(user_data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")


    new_user = User(
        username=user_data.username,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        middle_name=user_data.middle_name,
        password_hash=hash_password_bcrypt(user_data.password),
        is_active=True
    )


    user_role = db.query(Role).filter(Role.name == "user").first()
    if user_role:
        new_user.roles.append(user_role)

    db.add(new_user)
    db.commit()

    logger.info(f"User {user_data.username} registered successfully")
    return {"message": "User registered successfully"}


def check_permission(required_permission: str):
    def permission_checker(current_user: User = Depends(get_current_user)):
        print(f"CHECK PERMISSION: Checking '{required_permission}' for user '{current_user.username}'")

        user_permissions = set()
        for role in current_user.roles:
            for permission in role.permissions:
                user_permissions.add(permission.name)

        print(f" USER PERMISSIONS: {user_permissions}")

        if required_permission not in user_permissions:
            print(f"❌ PERMISSION DENIED: User lacks '{required_permission}'")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{required_permission}' required"
            )

        print(f"✅ PERMISSION GRANTED")
        return current_user

    return permission_checker