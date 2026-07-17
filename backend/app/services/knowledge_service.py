from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeArticle, ArticleTag
from app.models.tag import Tag


class KnowledgeService:
    """知识库服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_articles(
        self, provider: str = None, category: str = None,
        page: int = 1, page_size: int = 20
    ):
        """获取知识库文章列表"""
        query = select(KnowledgeArticle).where(
            KnowledgeArticle.status == "published"
        )

        if provider:
            query = query.where(KnowledgeArticle.provider == provider)
        if category:
            query = query.where(KnowledgeArticle.category == category)

        total = self.db.execute(
            select(func.count()).select_from(query.subquery())
        ).scalar() or 0

        query = query.order_by(KnowledgeArticle.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        articles = list(self.db.execute(query).scalars().all())

        items = []
        for article in articles:
            art_tags = []
            for art in self.db.execute(
                select(ArticleTag).where(ArticleTag.article_id == article.id)
            ).scalars().all():
                tag = self.db.get(Tag, art.tag_id)
                if tag:
                    art_tags.append({"id": tag.id, "name": tag.name})

            items.append({
                "id": article.id,
                "provider": article.provider,
                "category": article.category,
                "title": article.title,
                "summary": article.summary,
                "view_count": article.view_count,
                "like_count": article.like_count,
                "tags": art_tags,
                "created_at": article.created_at,
            })

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_article_detail(self, article_id: int):
        """获取文章详情"""
        article = self.db.get(KnowledgeArticle, article_id)
        if not article:
            raise ValueError("文章不存在")

        # 增加阅读计数
        article.view_count = (article.view_count or 0) + 1
        self.db.flush()

        art_tags = []
        for art in self.db.execute(
            select(ArticleTag).where(ArticleTag.article_id == article.id)
        ).scalars().all():
            tag = self.db.get(Tag, art.tag_id)
            if tag:
                art_tags.append({"id": tag.id, "name": tag.name})

        return {
            "id": article.id,
            "provider": article.provider,
            "category": article.category,
            "title": article.title,
            "summary": article.summary,
            "content": article.content,
            "view_count": article.view_count,
            "like_count": article.like_count,
            "source_url": article.source_url,
            "tags": art_tags,
            "created_at": article.created_at,
            "updated_at": article.updated_at,
            "published_at": article.published_at,
        }

    def search_articles(self, q: str):
        """搜索文章"""
        articles = list(self.db.execute(
            select(KnowledgeArticle).where(
                KnowledgeArticle.status == "published",
                or_(
                    KnowledgeArticle.title.ilike(f"%{q}%"),
                    KnowledgeArticle.summary.ilike(f"%{q}%"),
                    KnowledgeArticle.content.ilike(f"%{q}%"),
                )
            )
        ).scalars().all())

        items = []
        for article in articles:
            highlight = None
            if article.summary and q.lower() in article.summary.lower():
                idx = article.summary.lower().index(q.lower())
                start = max(0, idx - 20)
                end = min(len(article.summary), idx + len(q) + 20)
                hl = article.summary[start:end]
                highlight = hl.replace(q, f"<em>{q}</em>") if q in hl else hl

            items.append({
                "id": article.id,
                "title": article.title,
                "summary": article.summary,
                "highlight": highlight or article.summary,
                "provider": article.provider,
                "category": article.category,
            })

        return {"items": items, "total": len(items)}
