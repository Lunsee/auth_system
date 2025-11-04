from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from starlette import status

from .auth import check_permission
from app.db.database import get_db
from .models import Role, Permission, User
from pydantic import BaseModel

router = APIRouter()


class RoleCreate(BaseModel):
    name: str
    description: str | None = None


class AssignPermission(BaseModel):
    permission_name: str


class AssignRole(BaseModel):
    role_id: int


@router.get("/roles")
async def get_roles(
        current_user: User = Depends(check_permission("role:manage")),
        db: Session = Depends(get_db)
):
    roles = db.query(Role).options(joinedload(Role.permissions)).all()

    # Явно загружаем permissions для каждой роли
    result = []
    for role in roles:
        # Принудительно загружаем permissions
        db.refresh(role, attribute_names=['permissions'])

        role_data = {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "permissions": [
                {
                    "id": perm.id,
                    "name": perm.name,
                    "description": perm.description
                } for perm in role.permissions
            ]
        }
        result.append(role_data)

    return result


@router.post("/roles")
async def create_role(
        role_data: RoleCreate,
        current_user: User = Depends(check_permission("role:manage")),
        db: Session = Depends(get_db)
):
    role = Role(name=role_data.name, description=role_data.description)
    db.add(role)
    db.commit()
    return {"message": "Role created successfully"}



@router.get("/permissions")
async def get_permissions(
        current_user: User = Depends(check_permission("role:manage")),
        db: Session = Depends(get_db)
):
    return db.query(Permission).all()



@router.post("/roles/{role_id}/permissions")
async def add_permission_to_role(
        role_id: int,
        permission_data: AssignPermission,
        current_user: User = Depends(check_permission("role:manage")),
        db: Session = Depends(get_db)
):
    role = db.query(Role).filter(Role.id == role_id).first()
    permission = db.query(Permission).filter(Permission.name == permission_data.permission_name).first()

    if not role or not permission:
        raise HTTPException(status_code=404, detail="Role or permission not found")

    if permission not in role.permissions:
        role.permissions.append(permission)
        db.commit()

    return {"message": "Permission added to role"}


@router.post("/users/{user_id}/roles")
async def assign_role_to_user(
        user_id: int,
        role_data: AssignRole,
        current_user: User = Depends(check_permission("role:manage")),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    role = db.query(Role).filter(Role.id == role_data.role_id).first()

    if not user or not role:
        raise HTTPException(status_code=404, detail="User or role not found")

    if role not in user.roles:
        user.roles.append(role)
        db.commit()

    return {"message": "Role assigned to user"}


