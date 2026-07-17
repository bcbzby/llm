from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.certifications import router as cert_router
from app.api.questions import router as questions_router
from app.api.exams import router as exams_router
from app.api.reports import router as reports_router
from app.api.wrong_book import router as wrong_book_router
from app.api.knowledge import router as knowledge_router
from app.api.tags import router as tags_router
from app.crawler.admin_api import router as crawler_router
from app.api.contribute import router as contribute_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(cert_router)
api_router.include_router(questions_router)
api_router.include_router(exams_router)
api_router.include_router(reports_router)
api_router.include_router(wrong_book_router)
api_router.include_router(knowledge_router)
api_router.include_router(tags_router)
api_router.include_router(crawler_router)
api_router.include_router(contribute_router)
