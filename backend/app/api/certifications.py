from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.certification import Certification, Subject
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/certifications", tags=["认证与科目"])


@router.get("", response_model=ApiResponse)
def list_certifications(db: Session = Depends(get_db)):
    """获取所有认证列表"""
    certs = db.execute(
        select(Certification).where(Certification.is_active == True)
    ).scalars().all()

    data = []
    for cert in certs:
        subjects = [
            {"id": s.id, "name": s.name, "weight": float(s.weight)}
            for s in db.execute(
                select(Subject).where(Subject.certification_id == cert.id)
            ).scalars().all()
        ]
        data.append({
            "id": cert.id,
            "provider": cert.provider,
            "code": cert.code,
            "name": cert.name,
            "level": cert.level,
            "description": cert.description,
            "total_questions": cert.total_questions,
            "pass_score": cert.pass_score,
            "duration_min": cert.duration_min,
            "image_url": cert.image_url,
            "subjects": subjects,
        })

    return ApiResponse(data=data)
