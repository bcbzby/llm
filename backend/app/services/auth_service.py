from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import get_settings

security = HTTPBearer()
settings = get_settings()


class AuthService:
    """认证服务"""

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed.encode("utf-8")
        )

    @staticmethod
    def create_access_token(user_id: int, role: str) -> str:
        payload = {
            "sub": str(user_id),
            "role": role,
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(
                minutes=settings.jwt_access_token_expire_minutes
            ),
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

    @staticmethod
    def create_refresh_token(user_id: int) -> str:
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(
                days=settings.jwt_refresh_token_expire_days
            ),
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": 1002, "message": "token_expired"},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": 1003, "message": "token_invalid"},
            )


def get_current_user_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """FastAPI 依赖注入 - 获取当前用户 JWT payload"""
    payload = AuthService.decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 1003, "message": "token_invalid"},
        )
    return {
        "user_id": int(payload["sub"]),
        "role": payload.get("role", "learner"),
    }
