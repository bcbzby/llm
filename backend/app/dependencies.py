from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService, get_current_user_payload


def get_current_user(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db),
) -> User:
    """获取当前登录用户"""
    user = db.get(User, payload["user_id"])
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 1004, "message": "user_not_found"},
        )
    return user


def require_role(*roles: str):
    """角色权限检查依赖"""
    def role_checker(
        user: User = Depends(get_current_user),
    ) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": 1004, "message": "permission_denied"},
            )
        return user
    return role_checker
