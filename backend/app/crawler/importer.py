"""
Bulk import service - writes crawled questions to DB with dedup logic
"""
import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.question import Question, QuestionOption, QuestionTag
from app.models.tag import Tag
from app.models.certification import Subject
from app.crawler.parser import ParsedQuestion

logger = logging.getLogger(__name__)


class BulkImportResult:
    def __init__(self):
        self.total = 0
        self.imported = 0  # 新增
        self.skipped = 0   # 已存在跳过
        self.failed = 0    # 解析失败
        self.errors: list[str] = []


class QuestionImporter:
    """题目导入器"""

    def __init__(self, db: Session, default_subject_id: int, created_by: Optional[int] = None):
        self.db = db
        self.default_subject_id = default_subject_id
        self.created_by = created_by

    def import_parsed(self, parsed_list: list[ParsedQuestion], tag_map: Optional[dict] = None) -> BulkImportResult:
        """批量导入 ParsedQuestion 列表

        Args:
            parsed_list: 解析后的题目列表
            tag_map: 标签名 -> Tag.id 映射，None 则自动查找/创建
        """
        result = BulkImportResult()
        result.total = len(parsed_list)

        for pq in parsed_list:
            try:
                if self._is_duplicate(pq):
                    result.skipped += 1
                    continue

                question = self._create_question(pq)
                self._create_options(question.id, pq.options)
                self._link_tags(question.id, pq.tags, tag_map)
                result.imported += 1
            except Exception as e:
                result.failed += 1
                result.errors.append(str(e)[:200])
                logger.error(f"Import failed: {e}", exc_info=True)

        if result.imported > 0:
            self.db.commit()
            logger.info(f"Imported {result.imported}, skipped {result.skipped}, failed {result.failed}")
        else:
            self.db.flush()

        return result

    def _is_duplicate(self, pq: ParsedQuestion) -> bool:
        """去重检查：按 content + source + external_id 判断"""
        if pq.external_id:
            existing = self.db.execute(
                select(Question).where(
                    Question.external_id == pq.external_id,
                    Question.source == pq.source,
                )
            ).scalar_one_or_none()
            if existing:
                return True

        # 按 content 前 100 字符近似去重
        content_prefix = pq.content[:100]
        existing = self.db.execute(
            select(Question).where(
                Question.content.like(f"{content_prefix}%"),
                Question.source == pq.source,
            )
        ).scalar_one_or_none()
        return existing is not None

    def _create_question(self, pq: ParsedQuestion) -> Question:
        q = Question(
            subject_id=self.default_subject_id,
            question_type=pq.question_type,
            difficulty=pq.difficulty,
            content=pq.content,
            explanation=pq.explanation,
            reference_url=pq.reference_url,
            source=pq.source,
            external_id=pq.external_id,
            status="draft",  # 爬虫导入默认草稿，需人工审核发布
            is_verified=False,
            created_by=self.created_by,
        )
        self.db.add(q)
        self.db.flush()
        return q

    def _create_options(self, question_id: int, options: list[dict]):
        for order, opt in enumerate(options):
            qo = QuestionOption(
                question_id=question_id,
                option_key=opt["key"],
                content=opt["content"],
                is_correct=opt.get("is_correct", False),
                sort_order=order,
            )
            self.db.add(qo)

    def _link_tags(self, question_id: int, tag_names: list[str], tag_map: Optional[dict]):
        """关联标签，如果标签不存在则自动创建"""
        for name in tag_names:
            if not name or len(name) > 100:
                continue

            tag_id = None
            if tag_map and name in tag_map:
                tag_id = tag_map[name]
            else:
                # 查找或创建标签
                tag = self.db.execute(
                    select(Tag).where(Tag.name == name)
                ).scalar_one_or_none()
                if not tag:
                    tag = Tag(name=name, full_path=name, level=1)
                    self.db.add(tag)
                    self.db.flush()
                tag_id = tag.id
                if tag_map is not None:
                    tag_map[name] = tag_id

            # 检查关联是否已存在
            existing = self.db.execute(
                select(QuestionTag).where(
                    QuestionTag.question_id == question_id,
                    QuestionTag.tag_id == tag_id,
                )
            ).scalar_one_or_none()
            if not existing:
                self.db.add(QuestionTag(question_id=question_id, tag_id=tag_id))
