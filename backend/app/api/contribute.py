"""Question contribution API - users can submit/correct questions + admin review"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.question import Question, QuestionOption, QuestionTag
from app.models.tag import Tag
from app.models.certification import Subject, Certification
from app.schemas.common import ApiResponse
from pydantic import BaseModel
from datetime import datetime, timezone


class ContributeOption(BaseModel):
    key: str
    content: str
    is_correct: bool


class ContributeQuestion(BaseModel):
    subject_id: int
    question_type: str = "single_choice"
    difficulty: str = "medium"
    content: str
    options: list[ContributeOption]
    explanation: str = ""
    tags: list[str] = []


router = APIRouter(prefix="/questions/contribute", tags=["题目贡献"])


@router.post("", response_model=ApiResponse, status_code=201)
def submit_question(
    req: ContributeQuestion,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交新题目（状态为 pending，需审核）"""
    subj = db.get(Subject, req.subject_id)
    if not subj:
        raise HTTPException(status_code=400, detail="科目不存在")
    if len(req.options) < 2:
        raise HTTPException(status_code=400, detail="至少需要2个选项")
    if req.question_type == "single_choice":
        if sum(1 for o in req.options if o.is_correct) != 1:
            raise HTTPException(status_code=400, detail="单选题必须有且仅有一个正确答案")
    else:
        if sum(1 for o in req.options if o.is_correct) < 2:
            raise HTTPException(status_code=400, detail="多选题至少需要2个正确答案")

    q = Question(
        subject_id=req.subject_id, question_type=req.question_type,
        difficulty=req.difficulty, content=req.content, explanation=req.explanation,
        status="pending", is_verified=False, created_by=user.id,
    )
    db.add(q)
    db.flush()
    for opt in req.options:
        db.add(QuestionOption(question_id=q.id, option_key=opt.key, content=opt.content, is_correct=opt.is_correct, sort_order=ord(opt.key) - 65))
    for tag_name in req.tags:
        tag = db.execute(select(Tag).where(Tag.name == tag_name)).scalar_one_or_none()
        if not tag:
            tag = Tag(name=tag_name, full_path=tag_name, level=1)
            db.add(tag)
            db.flush()
        if not db.execute(select(QuestionTag).where(QuestionTag.question_id == q.id, QuestionTag.tag_id == tag.id)).scalar_one_or_none():
            db.add(QuestionTag(question_id=q.id, tag_id=tag.id))
    db.commit()
    db.refresh(q)
    return ApiResponse(data={"question_id": q.id, "status": q.status, "message": "题目已提交，待管理员审核"})


@router.get("/subjects", response_model=ApiResponse)
def list_subjects_for_contribution(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取可选科目列表（按认证分组）"""
    certs = db.execute(select(Certification)).scalars().all()
    result = []
    for cert in certs:
        subjects = db.execute(select(Subject).where(Subject.certification_id == cert.id)).scalars().all()
        if subjects:
            result.append({
                "cert_id": cert.id, "cert_name": cert.name,
                "subjects": [{"id": s.id, "name": s.name} for s in subjects],
            })
    return ApiResponse(data=result)


# ============================================================
# Admin review endpoints
# ============================================================

@router.get("/admin/list", response_model=ApiResponse)
def list_pending_questions(
    status: str = Query("pending", description="pending / approved / rejected"),
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """[管理员] 查看待审核/已通过/已拒绝的题目"""
    questions = db.execute(
        select(Question).where(Question.status == status)
        .order_by(Question.created_at.desc())
    ).scalars().all()

    result = []
    for q in questions:
        opts = db.execute(select(QuestionOption).where(QuestionOption.question_id == q.id).order_by(QuestionOption.sort_order)).scalars().all()
        subj = db.get(Subject, q.subject_id)
        cert = db.get(Certification, subj.certification_id) if subj else None
        submitter = db.get(User, q.created_by) if q.created_by else None
        result.append({
            "id": q.id,
            "cert_name": f"{cert.name} - {subj.name}" if cert and subj else "未知",
            "question_type": q.question_type,
            "difficulty": q.difficulty,
            "content": q.content,
            "explanation": q.explanation,
            "options": [{"key": o.option_key, "content": o.content, "is_correct": o.is_correct} for o in opts],
            "submitted_by": submitter.nickname if submitter else "未知",
            "created_at": q.created_at.isoformat() if q.created_at else "",
        })

    return ApiResponse(data={"questions": result, "total": len(result)})


class ReviewAction(BaseModel):
    action: str  # "approve" or "reject"


@router.post("/admin/review/{question_id}", response_model=ApiResponse)
def review_question(
    question_id: int,
    req: ReviewAction,
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """[管理员] 审核通过/拒绝题目"""
    q = db.get(Question, question_id)
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")

    if req.action == "approve":
        q.status = "published"
        q.is_verified = True
        msg = "题目已通过审核并发布"
    elif req.action == "reject":
        q.status = "rejected"
        msg = "题目已被拒绝"
    else:
        raise HTTPException(status_code=400, detail="无效操作，请使用 approve 或 reject")

    db.commit()
    return ApiResponse(data={"question_id": q.id, "status": q.status, "message": msg})
