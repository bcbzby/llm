from datetime import datetime, date
from sqlalchemy import String, Boolean, Integer, BigInteger, DateTime, Date, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class WrongBook(Base):
    __tablename__ = "wrong_book"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("questions.id"), nullable=False)
    wrong_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_wrong_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    is_mastered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mastered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now()
    )
    __table_args__ = (UniqueConstraint("user_id", "question_id"),)


class StudyProgress(Base):
    __tablename__ = "study_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    certification_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("certifications.id"), nullable=False)
    questions_answered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    questions_correct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    exam_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    exam_passed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    streak_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_study_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now()
    )
    __table_args__ = (UniqueConstraint("user_id", "certification_id"),)


class UserCertification(Base):
    __tablename__ = "user_certifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    certification_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("certifications.id"), nullable=False)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_certified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    certified_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    __table_args__ = (UniqueConstraint("user_id", "certification_id"),)


class QuestionFeedback(Base):
    __tablename__ = "question_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("questions.id"), nullable=False)
    feedback_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    resolved_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
