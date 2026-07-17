"""
Knowledge article importer - stores crawled/generated knowledge content to DB
"""
import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeArticle, ArticleTag
from app.models.tag import Tag

logger = logging.getLogger(__name__)


class KnowledgeImportResult:
    def __init__(self):
        self.total = 0
        self.imported = 0
        self.skipped = 0
        self.failed = 0
        self.errors: list[str] = []


class KnowledgeArticleData:
    """Data structure for a knowledge article to import"""
    def __init__(
        self,
        title: str,
        content: str,
        provider: str = "aws",
        category: str = "general",
        summary: str = "",
        tags: list[str] = None,
        source_url: str = "",
        status: str = "published",
    ):
        self.title = title
        self.content = content
        self.provider = provider
        self.category = category
        self.summary = summary or content[:200]
        self.tags = tags or []
        self.source_url = source_url
        self.status = status


class KnowledgeImporter:
    """Imports knowledge articles into database"""

    def __init__(self, db: Session, created_by: Optional[int] = None):
        self.db = db
        self.created_by = created_by

    def import_articles(self, articles: list[KnowledgeArticleData]) -> KnowledgeImportResult:
        """批量导入知识文章"""
        result = KnowledgeImportResult()
        result.total = len(articles)

        for art in articles:
            try:
                if self._is_duplicate(art):
                    result.skipped += 1
                    continue

                article = self._create_article(art)
                self._link_tags(article.id, art.tags)
                result.imported += 1
            except Exception as e:
                result.failed += 1
                result.errors.append(str(e)[:200])
                logger.error(f"Knowledge import failed: {e}", exc_info=True)

        if result.imported > 0:
            self.db.commit()
            logger.info(f"Imported {result.imported} articles, skipped {result.skipped}, failed {result.failed}")
        else:
            self.db.flush()

        return result

    def _is_duplicate(self, art: KnowledgeArticleData) -> bool:
        """按标题去重"""
        existing = self.db.execute(
            select(KnowledgeArticle).where(
                KnowledgeArticle.title == art.title,
                KnowledgeArticle.provider == art.provider,
            )
        ).scalar_one_or_none()
        return existing is not None

    def _create_article(self, art: KnowledgeArticleData) -> KnowledgeArticle:
        from datetime import datetime, timezone
        article = KnowledgeArticle(
            provider=art.provider,
            category=art.category,
            title=art.title,
            summary=art.summary,
            content=art.content,
            status=art.status,
            source_url=art.source_url,
            created_by=self.created_by,
            published_at=datetime.now(timezone.utc) if art.status == "published" else None,
        )
        self.db.add(article)
        self.db.flush()
        return article

    def _link_tags(self, article_id: int, tag_names: list[str]):
        """关联标签"""
        for name in tag_names:
            if not name or len(name) > 100:
                continue

            tag = self.db.execute(
                select(Tag).where(Tag.name == name)
            ).scalar()
            if not tag:
                tag = Tag(name=name, full_path=name, level=1)
                self.db.add(tag)
                self.db.flush()

            existing = self.db.execute(
                select(ArticleTag).where(
                    ArticleTag.article_id == article_id,
                    ArticleTag.tag_id == tag.id,
                )
            ).scalar_one_or_none()
            if not existing:
                self.db.add(ArticleTag(article_id=article_id, tag_id=tag.id))
