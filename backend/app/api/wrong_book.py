from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.study import WrongBook
from app.models.question import Question, QuestionOption
from app.models.certification import Subject
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/wrong-book", tags=["错题本"])


@router.get("", response_model=ApiResponse)
def list_wrong_book(
    certification_id: int = Query(None),
    is_mastered: bool = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取错题本列表"""
    query = select(WrongBook).where(WrongBook.user_id == user.id)
    if is_mastered is not None:
        query = query.where(WrongBook.is_mastered == is_mastered)

    query = query.order_by(WrongBook.last_wrong_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    wrong_items = list(db.execute(query).scalars().all())

    # 总数
    count_query = select(WrongBook).where(WrongBook.user_id == user.id)
    if is_mastered is not None:
        count_query = count_query.where(WrongBook.is_mastered == is_mastered)
    total = len(list(db.execute(count_query).scalars().all()))

    items = []
    for wb in wrong_items:
        question = db.get(Question, wb.question_id)
        if not question:
            continue

        if certification_id:
            subj = db.get(Subject, question.subject_id)
            if not subj or subj.certification_id != certification_id:
                continue

        options = [
            {"key": o.option_key, "content": o.content}
            for o in db.execute(
                select(QuestionOption).where(QuestionOption.question_id == question.id)
                .order_by(QuestionOption.sort_order)
            ).scalars().all()
        ]

        items.append({
            "id": wb.id,
            "question_id": question.id,
            "question": {
                "content": question.content,
                "question_type": question.question_type,
                "difficulty": question.difficulty,
                "options": options,
            },
            "wrong_count": wb.wrong_count,
            "last_wrong_at": wb.last_wrong_at,
            "is_mastered": wb.is_mastered,
        })

    return ApiResponse(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/{wrong_id}/master", response_model=ApiResponse)
def mark_mastered(
    wrong_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记错题已掌握"""
    wb = db.get(WrongBook, wrong_id)
    if not wb or wb.user_id != user.id:
        raise HTTPException(status_code=404, detail="错题记录不存在")

    wb.is_mastered = True
    from datetime import datetime, timezone
    wb.mastered_at = datetime.now(timezone.utc)
    db.commit()

    return ApiResponse(message="已标记为掌握")
