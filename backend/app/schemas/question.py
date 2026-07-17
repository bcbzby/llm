from datetime import datetime
from pydantic import BaseModel, Field


class OptionOut(BaseModel):
    key: str
    content: str

    class Config:
        from_attributes = True


class TagRef(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class SubjectRef(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class QuestionOut(BaseModel):
    id: int
    question_type: str
    difficulty: str
    content: str
    options: list[OptionOut] = []
    tags: list[TagRef] = []
    subject: SubjectRef | None = None

    class Config:
        from_attributes = True


class QuestionDetailOut(BaseModel):
    id: int
    question_type: str
    difficulty: str
    content: str
    options: list[OptionOut] = []
    explanation: str | None = None
    correct_keys: list[str] = []
    tags: list[TagRef] = []
    reference_url: str | None = None
    subject: SubjectRef | None = None

    class Config:
        from_attributes = True


class QuestionListData(BaseModel):
    items: list[QuestionOut] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
