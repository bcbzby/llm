import random

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.question import Question, QuestionOption, QuestionTag
from app.models.tag import Tag
from app.models.certification import Subject

# 匹配中文字符（用于按语言过滤题目）
_CJK_RANGE = "\u4e00-\u9fa5"


def _has_chinese(text: str) -> bool:
    """检测字符串是否包含中文字符"""
    if not text:
        return False
    return any("\u4e00" <= ch <= "\u9fa5" for ch in text)


class QuestionService:
    """题目服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_questions(
        self, subject_id: int = None, certification_id: int = None,
        difficulty: str = None,
        tag_ids: str = None, status: str = "published",
        page: int = 1, page_size: int = 20,
        lang: str = None, random_sample: bool = False,
        exclude_ids: str = None,
    ):
        """获取题目列表（不含答案）

        参数说明：
        - lang: "zh" 只返回含中文的题目，"en" 只返回不含中文的题目，None 不过滤
        - random_sample: True 时对匹配到的整个题库随机抽取 page_size 道题（用于刷题）
        - exclude_ids: 逗号分隔的题目ID，抽题时排除（避免连续重复）
        """
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

        exclude_id_set = set()
        if exclude_ids:
            exclude_id_set = {
                int(t) for t in exclude_ids.split(",") if t.strip().isdigit()
            }
            if exclude_id_set:
                query = query.where(Question.id.notin_(exclude_id_set))

        if random_sample:
            # 刷题模式：取出整个匹配池（仅ID+content用于语言过滤），
            # 随机抽取 page_size 道，保证覆盖全部题库而非仅最新的一页
            all_rows = list(self.db.execute(query).scalars().all())
            if lang == "zh":
                all_rows = [q for q in all_rows if _has_chinese(q.content)]
            elif lang == "en":
                all_rows = [q for q in all_rows if not _has_chinese(q.content)]

            total = len(all_rows)
            k = min(page_size, total)
            questions = random.sample(all_rows, k) if k > 0 else []

            items = self._serialize_questions(questions)
            return {"items": items, "total": total, "page": 1, "page_size": page_size}

        # 语言过滤（非随机模式）：先取全部匹配项做精确语言过滤，再分页
        if lang in ("zh", "en"):
            all_rows = list(
                self.db.execute(query.order_by(Question.id.desc())).scalars().all()
            )
            if lang == "zh":
                all_rows = [q for q in all_rows if _has_chinese(q.content)]
            else:
                all_rows = [q for q in all_rows if not _has_chinese(q.content)]
            total = len(all_rows)
            start = (page - 1) * page_size
            questions = all_rows[start:start + page_size]
            items = self._serialize_questions(questions)
            return {"items": items, "total": total, "page": page, "page_size": page_size}

        # 总数
        total = self.db.execute(
            select(func.count()).select_from(query.subquery())
        ).scalar() or 0

        # 分页
        query = query.order_by(Question.id.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        questions = list(self.db.execute(query).scalars().all())

        items = self._serialize_questions(questions)
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def _serialize_questions(self, questions):
        """将题目对象序列化为不含答案的字典列表"""
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
        return items

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
