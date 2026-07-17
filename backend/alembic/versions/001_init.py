"""initial migration - create all tables

Revision ID: 001
Revises:
Create Date: 2026-07-16
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("nickname", sa.String(100), nullable=False),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="learner"),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("oauth_provider", sa.String(20), nullable=True),
        sa.Column("oauth_id", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_role", "users", ["role"])

    # --- certifications ---
    op.create_table(
        "certifications",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("level", sa.String(30), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("total_questions", sa.Integer(), nullable=False, server_default="65"),
        sa.Column("pass_score", sa.Integer(), nullable=False, server_default="720"),
        sa.Column("duration_min", sa.Integer(), nullable=False, server_default="130"),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_cert_provider", "certifications", ["provider"])

    # --- subjects ---
    op.create_table(
        "subjects",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("certification_id", sa.BigInteger(), sa.ForeignKey("certifications.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("weight", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_subjects_cert", "subjects", ["certification_id"])

    # --- tags ---
    op.create_table(
        "tags",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("parent_id", sa.BigInteger(), sa.ForeignKey("tags.id"), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("full_path", sa.String(500), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_tags_parent", "tags", ["parent_id"])
    op.create_index("idx_tags_path", "tags", ["full_path"])

    # --- questions ---
    op.create_table(
        "questions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("subject_id", sa.BigInteger(), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("question_type", sa.String(20), nullable=False),
        sa.Column("difficulty", sa.String(10), nullable=False, server_default="medium"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("reference_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_questions_subject", "questions", ["subject_id"])
    op.create_index("idx_questions_status", "questions", ["status"])
    op.create_index("idx_questions_difficulty", "questions", ["difficulty"])

    # --- question_options ---
    op.create_table(
        "question_options",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("question_id", sa.BigInteger(), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("option_key", sa.String(5), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_qo_question", "question_options", ["question_id"])

    # --- question_tags ---
    op.create_table(
        "question_tags",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("question_id", sa.BigInteger(), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tag_id", sa.BigInteger(), sa.ForeignKey("tags.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("question_id", "tag_id"),
    )

    # --- exam_records ---
    op.create_table(
        "exam_records",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("certification_id", sa.BigInteger(), sa.ForeignKey("certifications.id"), nullable=False),
        sa.Column("exam_type", sa.String(20), nullable=False, server_default="practice"),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("wrong_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unanswered_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pass_score", sa.Integer(), nullable=True),
        sa.Column("is_passed", sa.Boolean(), nullable=True),
        sa.Column("duration_min", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("used_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="in_progress"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_exam_user", "exam_records", ["user_id"])
    op.create_index("idx_exam_cert", "exam_records", ["certification_id"])
    op.create_index("idx_exam_status", "exam_records", ["status"])
    op.create_index("idx_exam_user_cert", "exam_records", ["user_id", "certification_id"])

    # --- user_answers ---
    op.create_table(
        "user_answers",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("exam_record_id", sa.BigInteger(), sa.ForeignKey("exam_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.BigInteger(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("selected_options", postgresql.ARRAY(sa.String(5)), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("is_marked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_ua_exam", "user_answers", ["exam_record_id"])
    op.create_index("idx_ua_question", "user_answers", ["question_id"])

    # --- wrong_book ---
    op.create_table(
        "wrong_book",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("question_id", sa.BigInteger(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("wrong_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_wrong_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("is_mastered", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("mastered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "question_id"),
    )
    op.create_index("idx_wb_user", "wrong_book", ["user_id"])
    op.create_index("idx_wb_user_mastered", "wrong_book", ["user_id", "is_mastered"])

    # --- knowledge_articles ---
    op.create_table(
        "knowledge_articles",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("summary", sa.String(500), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("created_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_ka_provider", "knowledge_articles", ["provider"])
    op.create_index("idx_ka_category", "knowledge_articles", ["category"])
    op.create_index("idx_ka_provider_cat", "knowledge_articles", ["provider", "category"])

    # --- article_tags ---
    op.create_table(
        "article_tags",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("article_id", sa.BigInteger(), sa.ForeignKey("knowledge_articles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tag_id", sa.BigInteger(), sa.ForeignKey("tags.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("article_id", "tag_id"),
    )

    # --- article_versions ---
    op.create_table(
        "article_versions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("article_id", sa.BigInteger(), sa.ForeignKey("knowledge_articles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("change_note", sa.String(500), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("article_id", "version"),
    )

    # --- study_progress ---
    op.create_table(
        "study_progress",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("certification_id", sa.BigInteger(), sa.ForeignKey("certifications.id"), nullable=False),
        sa.Column("questions_answered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("questions_correct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("exam_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("exam_passed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("streak_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_study_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "certification_id"),
    )

    # --- user_certifications ---
    op.create_table(
        "user_certifications",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("certification_id", sa.BigInteger(), sa.ForeignKey("certifications.id"), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_certified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("certified_at", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "certification_id"),
    )

    # --- question_feedback ---
    op.create_table(
        "question_feedback",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("question_id", sa.BigInteger(), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("feedback_type", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("resolved_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("question_feedback")
    op.drop_table("user_certifications")
    op.drop_table("study_progress")
    op.drop_table("article_versions")
    op.drop_table("article_tags")
    op.drop_table("knowledge_articles")
    op.drop_table("wrong_book")
    op.drop_table("user_answers")
    op.drop_table("exam_records")
    op.drop_table("question_tags")
    op.drop_table("question_options")
    op.drop_table("questions")
    op.drop_table("tags")
    op.drop_table("subjects")
    op.drop_table("certifications")
    op.drop_table("users")
