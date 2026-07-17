from datetime import datetime
from sqlalchemy import String, Boolean, Integer, BigInteger, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class ExamRecord(Base):
    __tablename__ = "exam_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    certification_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("certifications.id"), nullable=False)
    exam_type: Mapped[str] = mapped_column(String(20), nullable=False, default="practice")
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wrong_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unanswered_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pass_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    used_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="in_progress")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class UserAnswer(Base):
    __tablename__ = "user_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exam_record_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("exam_records.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("questions.id"), nullable=False)
    selected_options: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_marked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
