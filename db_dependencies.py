from database import SessionLocal
from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from config import SECRET_KEY, ALGORITHM
from fastapi.security import HTTPAuthorizationCredentials
from security import bearer_scheme
from models import User, BlacklistedToken
from sqlalchemy.orm import Session


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ✅ AUTHENTICATION (USER OR ADMIN)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):

    token = credentials.credentials

    try:

        # 🔹 Check blacklisted token
        blacklisted_token = db.query(BlacklistedToken).filter(
            BlacklistedToken.token == token
        ).first()

        if blacklisted_token:

            raise HTTPException(
                status_code=401,
                detail="Token expired. Please login again"
            )

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")
        role = payload.get("role")
        user_id = payload.get("id")
        employee_id = payload.get("employee_id")

        if not email:
            raise HTTPException(
                status_code=401,
                detail="Invalid token payload"
            )

        # 🔹 Handle hardcoded super admin
        if role == "super admin":

            return {
                "id": user_id,
                "employee_id": employee_id,
                "email": email,
                "role": role
            }

        # 🔹 Normal DB users
        user = db.query(User).filter(
            User.email == email
        ).first()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )

        return {
            "id": user.id,
            "employee_id": user.employee_id,
            "email": user.email,
            "role": user.role
        }

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


# ✅ ADMIN AUTHORIZATION
def admin_only(
    current_user=Depends(get_current_user)
):

    if current_user["role"] not in ["admin", "super admin"]:

        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_user
