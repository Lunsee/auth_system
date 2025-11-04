from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.auth import get_current_user, check_permission
from app.db.database import get_db
from app.models import User
from pydantic import BaseModel

router = APIRouter()


class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None


@router.get("/me")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "middle_name": current_user.middle_name,
        "is_active": current_user.is_active,
        "roles": [role.name for role in current_user.roles]
    }


@router.put("/me")
async def update_my_profile(
        user_data: UserUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    update_data = user_data.dict(exclude_unset=True)


    if 'username' in update_data and update_data['username'] != current_user.username:
        existing_user = db.query(User).filter(
            User.username == update_data['username']
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")


    if 'email' in update_data and update_data['email'] != current_user.email:
        existing_email = db.query(User).filter(
            User.email == update_data['email']
        ).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already taken")


    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.commit()
    return {"message": "Profile updated successfully"}



@router.delete("/me")
async def delete_my_account(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    current_user.is_active = False
    db.commit()
    return {"message": "Account deactivated successfully"}


# АДМИНСКИЕ ЭНДПОИНТЫ:
@router.get("/")
async def get_all_users(
        current_user: User = Depends(check_permission("user:read")),
        db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "username": user.username,
            "is_active": user.is_active,
            "roles": [role.name for role in user.roles]
        } for user in users
    ]


@router.delete("/{user_id}")
async def delete_user(
        user_id: int,
        current_user: User = Depends(check_permission("user:delete")),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": "User permanently deleted"}