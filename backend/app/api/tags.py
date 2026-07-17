from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.tag import Tag
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/tags", tags=["标签"])


@router.get("", response_model=ApiResponse)
def list_tags(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取所有标签"""
    tags = db.execute(select(Tag).order_by(Tag.full_path)).scalars().all()
    return ApiResponse(data=[
        {"id": t.id, "name": t.name, "full_path": t.full_path, "level": t.level}
        for t in tags
    ])
