from pydantic import BaseModel


class SubjectBreakdown(BaseModel):
    subject_id: int
    subject_name: str
    weight: float
    total: int
    correct: int
    correct_rate: str


class TagBreakdown(BaseModel):
    tag_id: int
    tag_name: str
    total: int
    correct: int
    correct_rate: str


class WeaknessTag(BaseModel):
    tag_id: int
    tag_name: str
    correct_rate: str
    suggested_action: str


class StrengthTag(BaseModel):
    tag_id: int
    tag_name: str
    correct_rate: str
    suggested_action: str


class HistoryPoint(BaseModel):
    date: str
    score: int


class ExamSummary(BaseModel):
    exam_id: int
    title: str | None = None
    score: int
    total_score: int
    correct_rate: str
    is_passed: bool | None = None
    gap_to_pass: int = 0


class ReportOut(BaseModel):
    exam_summary: ExamSummary
    subject_breakdown: list[SubjectBreakdown] = []
    tag_breakdown: list[TagBreakdown] = []
    weakness_tags: list[WeaknessTag] = []
    strength_tags: list[StrengthTag] = []
    history_trend: list[HistoryPoint] = []
