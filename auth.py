from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from models import ClientUser, BlacklistedToken
from models import User
from models import Client
from schemas import LoginRequest, TokenResponse
from db_dependencies import get_db
from security import verify_password
from config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/auth", tags=["Auth"])
bearer_scheme = HTTPBearer()

def create_token(data: dict, minutes: int) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(data: LoginRequest, db: Session = Depends(get_db)):

    email = data.email.strip().lower()

    # ==================================================
    # SUPER ADMIN LOGIN
    # ==================================================

    if email == "admin@msstechno.com" and data.password == "adminmss":

        access_token = create_token(
            {
                "sub": email,
                "role": "super admin",
                "id": 999999,
                "employee_id": "MSS000"
            },
            ACCESS_TOKEN_EXPIRE_MINUTES,
        )

        refresh_token = create_token(
            {
                "sub": email,
                "type": "refresh",
                "id": 999999,
                "employee_id": "MSS000"
            },
            REFRESH_TOKEN_EXPIRE_MINUTES,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "role": "super admin",
            "employee_id": "MSS000"
        }

    # ==================================================
    # USERS LOGIN
    # ==================================================

    user = db.query(
        User.id,
        User.email,
        User.password_hash,
        User.role,
        User.employee_id
    ).filter(
        User.email == email
    ).first()

    if user:

        # Password hash verification
        if not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )

        access_token = create_token(
            {
                "sub": user.email,
                "role": user.role,
                "id": user.id,
                "employee_id": user.employee_id,
                "user_type": "user"
            },
            ACCESS_TOKEN_EXPIRE_MINUTES,
        )

        refresh_token = create_token(
            {
                "sub": user.email,
                "type": "refresh",
                "id": user.id,
                "employee_id": user.employee_id,
                "user_type": "user"
            },
            REFRESH_TOKEN_EXPIRE_MINUTES,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "role": user.role,
            "employee_id": user.employee_id,
            "user_type": "user"
        }

    # ==================================================
    # CLIENT LOGIN
    # ==================================================

    client = db.query(
        Client.id,
        Client.client_name,
        Client.email,
        Client.password,
        Client.technology,
        Client.status
    ).filter(
        Client.email == email
    ).first()

    if client:

        # Plain password check
        if data.password != client.password:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )

        access_token = create_token(
            {
                "sub": client.email,
                "role": "client",
                "id": client.id,
                "user_type": "client"
            },
            ACCESS_TOKEN_EXPIRE_MINUTES,
        )

        refresh_token = create_token(
            {
                "sub": client.email,
                "type": "refresh",
                "id": client.id,
                "user_type": "client"
            },
            REFRESH_TOKEN_EXPIRE_MINUTES,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "role": "client",
            "client_id": client.id,
            "user_type": "client",
            "name": client.client_name,
            "email": client.email,
            "technology": client.technology,
            "status": client.status
}

    # ==================================================
    # INVALID LOGIN
    # ==================================================

    raise HTTPException(
        status_code=401,
        detail="Invalid credentials"
    )

@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):

    token = credentials.credentials

    blacklisted_token = BlacklistedToken(
        token=token
    )

    db.add(blacklisted_token)

    db.commit()

    return {
        "message": "Logout successful"
    }
