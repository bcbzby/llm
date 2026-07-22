from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse
from app.services.question_service import QuestionService

router = APIRouter(prefix="/questions", tags=["题库"])


@router.get("", response_model=ApiResponse)
def list_questions(
    subject_id: int = Query(None, description="科目ID"),
    certification_id: int = Query(None, description="认证ID"),
    difficulty: str = Query(None, description="难度: easy/medium/hard"),
    tag_ids: str = Query(None, description="标签ID，逗号分隔"),
    status: str = Query("published", description="状态"),
    lang: str = Query(None, description="语言过滤: zh(仅中文题) / en(仅英文题)"),
    random_sample: bool = Query(False, description="是否从整个题库随机抽题（刷题模式）"),
    exclude_ids: str = Query(None, description="抽题时排除的题目ID，逗号分隔"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取题目列表（不含答案）"""
    service = QuestionService(db)
    data = service.get_questions(
        subject_id=subject_id, certification_id=certification_id,
        difficulty=difficulty,
        tag_ids=tag_ids, status=status,
        page=page, page_size=page_size,
        lang=lang, random_sample=random_sample, exclude_ids=exclude_ids,
    )
    return ApiResponse(data=data)


@router.get("/{question_id}", response_model=ApiResponse)
def get_question(
    question_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取题目详情（含答案和解析）"""
    service = QuestionService(db)
    try:
        data = service.get_question_detail(question_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ApiResponse(data=data)
