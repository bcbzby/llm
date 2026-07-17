from datetime import datetime
from pydantic import BaseModel, Field


class ExamCreate(BaseModel):
    certification_id: int
    exam_type: str = "mock"
    question_count: int | None = None
    duration_min: int | None = None
    custom_tags: list[int] = []


class AnswerItem(BaseModel):
    question_id: int
    selected_keys: list[str] = []


class ExamSubmit(BaseModel):
    answers: list[AnswerItem]
    used_seconds: int


class ExamQuestionOut(BaseModel):
    id: int
    question_type: str
    content: str
    options: list[dict] = []


class ExamCreatedOut(BaseModel):
    exam_id: int
    certification: dict | None = None
    total_questions: int
    duration_min: int
    questions: list[ExamQuestionOut] = []
    status: str
    started_at: datetime


class ExamSubmitResult(BaseModel):
    exam_id: int
    status: str
    total_questions: int
    correct_count: int
    wrong_count: int
    unanswered_count: int
    score: int
    total_score: int
    pass_score: int | None = None
    is_passed: bool | None = None
    used_seconds: int
    completed_at: datetime | None = None


class QuestionResult(BaseModel):
    question_id: int
    content: str
    question_type: str
    selected_keys: list[str] = []
    correct_keys: list[str] = []
    is_correct: bool
    explanation: str | None = None


class ExamResultOut(BaseModel):
    exam_id: int
    title: str | None = None
    status: str
    total_questions: int
    correct_count: int
    wrong_count: int
    unanswered_count: int
    score: int
    total_score: int
    pass_score: int | None = None
    is_passed: bool | None = None
    gap_to_pass: int = 0
    used_seconds: int
    duration_min: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    question_results: list[QuestionResult] = []
