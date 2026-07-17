from app.tasks.celery_app import celery_app
from app.services.report_service import ReportService
from app.database import AsyncSessionLocal


@celery_app.task
def generate_report_task(exam_id: int):
    """异步生成评估报告"""
    import asyncio
    async def _run():
        async with AsyncSessionLocal() as db:
            service = ReportService(db)
            return await service.get_exam_report(exam_id)
    return asyncio.run(_run())


@celery_app.task
def cleanup_expired_exams():
    """清理过期考试"""
    import asyncio
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import select

    async def _run():
        async with AsyncSessionLocal() as db:
            from app.models.exam import ExamRecord
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            result = await db.execute(
                select(ExamRecord).where(
                    ExamRecord.status == "in_progress",
                    ExamRecord.created_at < cutoff,
                )
            )
            exams = list(result.scalars().all())
            for exam in exams:
                exam.status = "expired"
            await db.commit()
            return len(exams)

    return asyncio.run(_run())
