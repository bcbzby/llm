from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserRegister, UserLogin, TokenRefresh,
    RegisterOut, LoginOut, TokenRefreshOut, UserOut,
)
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService, get_current_user_payload

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=ApiResponse, status_code=201)
def register(req: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    existing = db.execute(select(User).where(User.email == req.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail={"code": 1001, "message": "email_already_exists"})

    user = User(
        email=req.email,
        password_hash=AuthService.hash_password(req.password),
        nickname=req.nickname,
        role="learner",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return ApiResponse(data=RegisterOut(
        user_id=user.id,
        email=user.email,
        nickname=user.nickname,
        role=user.role,
        created_at=user.created_at,
    ))


@router.post("/login", response_model=ApiResponse)
def login(req: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.execute(select(User).where(User.email == req.email)).scalar_one_or_none()
    if not user or not user.password_hash:
        raise HTTPException(
            status_code=401,
            detail={"code": 1001, "message": "invalid_credentials"},
        )

    if not AuthService.verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail={"code": 1001, "message": "invalid_credentials"},
        )

    user.last_login_at = datetime.now(timezone.utc)
    db.flush()
    db.commit()

    access_token = AuthService.create_access_token(user.id, user.role)
    refresh_token = AuthService.create_refresh_token(user.id)

    return ApiResponse(data=LoginOut(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800,
        user=UserOut(
            id=user.id,
            email=user.email,
            nickname=user.nickname,
            role=user.role,
            avatar_url=user.avatar_url,
        ),
    ))


@router.post("/refresh", response_model=ApiResponse)
def refresh_token(req: TokenRefresh):
    """刷新 Token"""
    payload = AuthService.decode_token(req.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=401,
            detail={"code": 1003, "message": "token_invalid"},
        )

    user_id = int(payload["sub"])
    access_token = AuthService.create_access_token(user_id, "learner")

    return ApiResponse(data=TokenRefreshOut(
        access_token=access_token,
        expires_in=1800,
    ))


@router.get("/me", response_model=ApiResponse)
def get_me(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db),
):
    """获取当前用户信息"""
    user = db.get(User, payload["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail={"code": 1004, "message": "user_not_found"})

    return ApiResponse(data=UserOut(
        id=user.id,
        email=user.email,
        nickname=user.nickname,
        role=user.role,
        avatar_url=user.avatar_url,
    ))
