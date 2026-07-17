from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.exam import ExamRecord
from app.models.question import QuestionOption
from app.models.certification import Certification
from app.schemas.exam import ExamCreate, ExamSubmit
from app.schemas.common import ApiResponse
from app.services.exam_service import ExamService

router = APIRouter(prefix="/exams", tags=["考试"])


@router.post("", response_model=ApiResponse, status_code=201)
def create_exam(
    req: ExamCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建模拟考试"""
    service = ExamService(db)
    try:
        exam, questions = service.create_exam(user.id, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    question_list = []
    for q in questions:
        options = [
            {"key": o.option_key, "content": o.content}
            for o in db.execute(
                select(QuestionOption).where(QuestionOption.question_id == q.id)
                .order_by(QuestionOption.sort_order)
            ).scalars().all()
        ]
        question_list.append({
            "id": q.id,
            "question_type": q.question_type,
            "content": q.content,
            "options": options,
        })

    cert = db.get(Certification, exam.certification_id)

    return ApiResponse(data={
        "exam_id": exam.id,
        "certification": {
            "id": cert.id,
            "name": cert.name,
            "pass_score": cert.pass_score,
        } if cert else None,
        "total_questions": exam.total_questions,
        "duration_min": exam.duration_min,
        "questions": question_list,
        "status": exam.status,
        "started_at": exam.started_at,
    })


@router.post("/{exam_id}/submit", response_model=ApiResponse)
def submit_exam(
    exam_id: int,
    req: ExamSubmit,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """交卷评分"""
    service = ExamService(db)
    try:
        exam = service.submit_exam(exam_id, user.id, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ApiResponse(data={
        "exam_id": exam.id,
        "status": exam.status,
        "total_questions": exam.total_questions,
        "correct_count": exam.correct_count,
        "wrong_count": exam.wrong_count,
        "unanswered_count": exam.unanswered_count,
        "score": exam.score,
        "total_score": exam.total_score,
        "pass_score": exam.pass_score,
        "is_passed": exam.is_passed,
        "used_seconds": exam.used_seconds,
        "completed_at": exam.completed_at,
    })


@router.get("/{exam_id}/result", response_model=ApiResponse)
def get_exam_result(
    exam_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取考试结果详情"""
    from app.services.report_service import ReportService
    service = ReportService(db)
    try:
        data = service.get_exam_result(exam_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return ApiResponse(data=data)


@router.get("/history", response_model=ApiResponse)
def get_exam_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取用户考试历史"""
    exams = db.execute(
        select(ExamRecord).where(ExamRecord.user_id == user.id)
        .order_by(ExamRecord.created_at.desc())
    ).scalars().all()

    return ApiResponse(data=[
        {
            "exam_id": e.id,
            "title": e.title,
            "exam_type": e.exam_type,
            "score": e.score,
            "total_score": e.total_score,
            "is_passed": e.is_passed,
            "correct_count": e.correct_count,
            "total_questions": e.total_questions,
            "status": e.status,
            "started_at": e.started_at,
            "completed_at": e.completed_at,
        }
        for e in exams
    ])
