from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.services.report_service import ReportService


@celery_app.task
def generate_report_task(exam_id: int):
    """异步生成评估报告"""
    db = SessionLocal()
    try:
        service = ReportService(db)
        return service.get_exam_report(exam_id)
    finally:
        db.close()


@celery_app.task
def cleanup_expired_exams():
    """清理过期考试"""
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import select

    db = SessionLocal()
    try:
        from app.models.exam import ExamRecord
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        result = db.execute(
            select(ExamRecord).where(
                ExamRecord.status == "in_progress",
                ExamRecord.created_at < cutoff,
            )
        )
        exams = list(result.scalars().all())
        for exam in exams:
            exam.status = "expired"
        db.commit()
        return len(exams)
    finally:
        db.close()
