from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["知识库"])


@router.get("", response_model=ApiResponse)
def list_knowledge(
    provider: str = Query(None),
    category: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取知识库列表"""
    service = KnowledgeService(db)
    data = service.get_articles(provider=provider, category=category, page=page, page_size=page_size)
    return ApiResponse(data=data)


@router.get("/search", response_model=ApiResponse)
def search_knowledge(
    q: str = Query(..., min_length=1),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """搜索知识库"""
    service = KnowledgeService(db)
    data = service.search_articles(q)
    return ApiResponse(data=data)


@router.get("/{article_id}", response_model=ApiResponse)
def get_knowledge_detail(
    article_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取文章详情"""
    service = KnowledgeService(db)
    try:
        data = service.get_article_detail(article_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ApiResponse(data=data)
