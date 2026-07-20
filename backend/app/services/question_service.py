from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.question import Question, QuestionOption, QuestionTag
from app.models.tag import Tag
from app.models.certification import Subject


class QuestionService:
    """题目服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_questions(
        self, subject_id: int = None, certification_id: int = None,
        difficulty: str = None,
        tag_ids: str = None, status: str = "published",
        page: int = 1, page_size: int = 20
    ):
        """获取题目列表（不含答案）"""
        query = select(Question).where(Question.status == status)

        if subject_id:
            query = query.where(Question.subject_id == subject_id)
        if certification_id:
            # 查找该认证下的所有科目
            subquery = select(Subject.id).where(
                Subject.certification_id == certification_id
            ).subquery()
            query = query.where(Question.subject_id.in_(select(subquery.c.id)))
        if difficulty:
            query = query.where(Question.difficulty == difficulty)
        if tag_ids:
            tag_id_list = [int(t) for t in tag_ids.split(",") if t.strip().isdigit()]
            if tag_id_list:
                query = query.where(
                    Question.id.in_(
                        select(QuestionTag.question_id).where(
                            QuestionTag.tag_id.in_(tag_id_list)
                        )
                    )
                )

        # 总数
        total = self.db.execute(
            select(func.count()).select_from(query.subquery())
        ).scalar() or 0

        # 分页
        query = query.order_by(Question.id.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        questions = list(self.db.execute(query).scalars().all())

        items = []
        for q in questions:
            options = [
                {"key": o.option_key, "content": o.content}
                for o in self.db.execute(
                    select(QuestionOption).where(QuestionOption.question_id == q.id)
                    .order_by(QuestionOption.sort_order)
                ).scalars().all()
            ]

            q_tags = []
            for qt in self.db.execute(
                select(QuestionTag).where(QuestionTag.question_id == q.id)
            ).scalars().all():
                tag = self.db.get(Tag, qt.tag_id)
                if tag:
                    q_tags.append({"id": tag.id, "name": tag.name})

            subj = self.db.get(Subject, q.subject_id)

            items.append({
                "id": q.id,
                "question_type": q.question_type,
                "difficulty": q.difficulty,
                "content": q.content,
                "options": options,
                "tags": q_tags,
                "subject": {"id": subj.id, "name": subj.name} if subj else None,
            })

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_question_detail(self, question_id: int):
        """获取题目详情（含答案和解析）"""
        q = self.db.get(Question, question_id)
        if not q:
            raise ValueError("题目不存在")

        all_options = list(self.db.execute(
            select(QuestionOption).where(QuestionOption.question_id == q.id)
            .order_by(QuestionOption.sort_order)
        ).scalars().all())

        options = [{"key": o.option_key, "content": o.content} for o in all_options]
        correct_keys = sorted([o.option_key for o in all_options if o.is_correct])

        q_tags = []
        for qt in self.db.execute(
            select(QuestionTag).where(QuestionTag.question_id == q.id)
        ).scalars().all():
            tag = self.db.get(Tag, qt.tag_id)
            if tag:
                q_tags.append({"id": tag.id, "name": tag.name})

        subj = self.db.get(Subject, q.subject_id)

        return {
            "id": q.id,
            "question_type": q.question_type,
            "difficulty": q.difficulty,
            "content": q.content,
            "options": options,
            "explanation": q.explanation,
            "correct_keys": correct_keys,
            "tags": q_tags,
            "reference_url": q.reference_url,
            "subject": {"id": subj.id, "name": subj.name} if subj else None,
        }
