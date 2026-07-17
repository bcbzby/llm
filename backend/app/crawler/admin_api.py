"""Admin API - crawler management endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.question import Question
from app.models.tag import Tag
from app.schemas.common import ApiResponse
from app.crawler.service import CrawlerService
from app.crawler.sources import PREDEFINED_SOURCES

router = APIRouter(prefix="/admin/crawler", tags=["admin-crawler"])


@router.post("/crawl", response_model=ApiResponse)
def start_crawl(
    urls: list[str] = Query(..., description="Target URLs to crawl"),
    source: str = Query("web", description="Source identifier"),
    subject_id: int = Query(1, description="Target subject ID"),
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """[Admin] Crawl questions from URLs and import to database"""
    if not urls:
        raise HTTPException(status_code=400, detail="At least one URL required")

    tags_result = db.execute(select(Tag)).scalars().all()
    tag_map = {t.name: t.id for t in tags_result}

    service = CrawlerService(db, user_id=user.id)
    result = service.crawl_urls(urls, source=source, subject_id=subject_id, tag_map=tag_map)

    return ApiResponse(data={
        "total": result.total,
        "imported": result.imported,
        "skipped": result.skipped,
        "failed": result.failed,
        "errors": result.errors[:10],
    })


@router.post("/crawl/paginated", response_model=ApiResponse)
def start_paginated_crawl(
    base_url: str = Query(..., description="Paginated listing URL"),
    source: str = Query("web", description="Source identifier"),
    subject_id: int = Query(1, description="Target subject ID"),
    max_pages: int = Query(50, ge=1, le=200, description="Max pages to crawl"),
    url_template: str = Query(None, description="URL template like https://example.com/q/{}"),
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """[Admin] Crawl paginated question listing"""
    tags_result = db.execute(select(Tag)).scalars().all()
    tag_map = {t.name: t.id for t in tags_result}

    service = CrawlerService(db, user_id=user.id)
    result = service.crawl_paginated(
        base_url, source=source, subject_id=subject_id,
        max_pages=max_pages, url_template=url_template, tag_map=tag_map,
    )

    return ApiResponse(data={
        "total": result.total,
        "imported": result.imported,
        "skipped": result.skipped,
        "failed": result.failed,
        "errors": result.errors[:10],
    })


@router.get("/sources", response_model=ApiResponse)
def list_sources(
    user: User = Depends(require_role("admin")),
):
    """[Admin] List available predefined sources"""
    sources = []
    for key, config in PREDEFINED_SOURCES.items():
        sources.append({
            "key": key,
            "label": config["label"],
            "type": config["type"],
            "url_count": len(config.get("urls", [])),
            "description": config.get("description", ""),
        })
    return ApiResponse(data=sources)


@router.post("/sources/{source_key}", response_model=ApiResponse)
def crawl_predefined(
    source_key: str,
    subject_id: int = Query(1, description="Target subject ID"),
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """[Admin] Crawl a predefined source"""
    service = CrawlerService(db, user_id=user.id)
    try:
        result = service.crawl_predefined_source(source_key, subject_id=subject_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ApiResponse(data={
        "total": result.total,
        "imported": result.imported,
        "skipped": result.skipped,
        "failed": result.failed,
        "errors": result.errors[:10],
    })


@router.get("/stats", response_model=ApiResponse)
def crawler_stats(
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """[Admin] View question stats by source"""
    result = db.execute(
        select(Question.source, func.count(Question.id))
        .where(Question.source.isnot(None))
        .group_by(Question.source)
    ).all()

    stats = [{"source": row[0], "count": row[1]} for row in result]

    total = db.execute(select(func.count(Question.id))).scalar() or 0
    verified = db.execute(select(func.count(Question.id)).where(Question.is_verified == True)).scalar() or 0

    return ApiResponse(data={
        "total_questions": total,
        "verified_questions": verified,
        "by_source": stats,
    })
