from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["评估报告"])


@router.get("/{exam_id}", response_model=ApiResponse)
def get_report(
    exam_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取考试评估报告"""
    service = ReportService(db)
    try:
        data = service.get_exam_report(exam_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    data["history_trend"] = []
    return ApiResponse(data=data)
