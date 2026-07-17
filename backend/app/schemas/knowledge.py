from datetime import datetime
from pydantic import BaseModel


class KnowledgeArticleOut(BaseModel):
    id: int
    provider: str | None = None
    category: str
    title: str
    summary: str | None = None
    view_count: int = 0
    like_count: int = 0
    tags: list[dict] = []
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class KnowledgeDetailOut(BaseModel):
    id: int
    provider: str | None = None
    category: str
    title: str
    summary: str | None = None
    content: str
    view_count: int = 0
    like_count: int = 0
    source_url: str | None = None
    tags: list[dict] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None
    published_at: datetime | None = None

    class Config:
        from_attributes = True


class KnowledgeSearchResult(BaseModel):
    id: int
    title: str
    summary: str | None = None
    highlight: str | None = None
    provider: str | None = None
    category: str
