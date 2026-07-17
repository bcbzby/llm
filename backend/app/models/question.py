from datetime import datetime
from sqlalchemy import String, Boolean, Text, Integer, BigInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("subjects.id"), nullable=False)
    question_type: Mapped[str] = mapped_column(String(20), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="题目来源标识，如 examtopics, aws_whitepapers")
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="来源侧原始ID，用于去重")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now()
    )

    options: Mapped[list["QuestionOption"]] = relationship(back_populates="question", lazy="selectin")
    tags: Mapped[list["QuestionTag"]] = relationship(back_populates="question", lazy="selectin")


class QuestionOption(Base):
    __tablename__ = "question_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    option_key: Mapped[str] = mapped_column(String(5), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    question: Mapped["Question"] = relationship(back_populates="options", lazy="selectin")


class QuestionTag(Base):
    __tablename__ = "question_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    tag_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    __table_args__ = (UniqueConstraint("question_id", "tag_id"),)

    question: Mapped["Question"] = relationship(back_populates="tags", lazy="selectin")
