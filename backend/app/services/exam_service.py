import random
from datetime import datetime, timezone
from typing import List
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.certification import Certification, Subject
from app.models.question import Question, QuestionOption, QuestionTag
from app.models.exam import ExamRecord, UserAnswer
from app.models.study import WrongBook, StudyProgress
from app.schemas.exam import ExamCreate, ExamSubmit


class ExamService:
    """考试引擎 - 核心业务"""

    def __init__(self, db: Session):
        self.db = db

    def create_exam(
        self, user_id: int, req: ExamCreate
    ) -> tuple:
        """创建考试：校验认证 → 抽题 → 创建记录"""
        # 1. 获取认证信息
        cert = self.db.get(Certification, req.certification_id)
        if not cert or not cert.is_active:
            raise ValueError("认证不存在或已下线")

        # 2. 确定题量和时长
        question_count = req.question_count or cert.total_questions
        duration_min = req.duration_min or cert.duration_min

        # 3. 获取该认证下所有已发布的题目
        subquery = select(Subject.id).where(
            Subject.certification_id == cert.id
        ).subquery()

        query = select(Question).where(
            Question.subject_id.in_(select(subquery.c.id)),
            Question.status == "published"
        )

        # 如果指定了自定义知识点标签，进一步筛选
        if req.custom_tags:
            query = query.where(
                Question.id.in_(
                    select(QuestionTag.question_id).where(
                        QuestionTag.tag_id.in_(req.custom_tags)
                    )
                )
            )

        all_questions = list(self.db.execute(query).scalars().all())

        # 随机打乱并取指定数量
        selected = random.sample(
            all_questions,
            min(question_count, len(all_questions))
        )

        # 4. 创建考试记录
        exam = ExamRecord(
            user_id=user_id,
            certification_id=cert.id,
            exam_type=req.exam_type,
            title=f"{cert.name} 模拟考试",
            total_questions=len(selected),
            total_score=1000,
            pass_score=cert.pass_score,
            duration_min=duration_min,
            status="in_progress",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(exam)
        self.db.flush()
        self.db.commit()

        return exam, selected

    def submit_exam(
        self, exam_id: int, user_id: int, req: ExamSubmit
    ) -> ExamRecord:
        """交卷：校验 → 逐题评分 → 更新记录 → 错题本 → 学习进度"""
        exam = self.db.get(ExamRecord, exam_id)
        if not exam or exam.user_id != user_id:
            raise ValueError("考试不存在")
        if exam.status != "in_progress":
            raise ValueError("考试已交卷")

        # 校验是否超时（加5分钟缓冲）
        elapsed = req.used_seconds
        if elapsed > exam.duration_min * 60 + 300:
            raise ValueError("考试已超时")

        # 逐题评分
        correct_count = 0
        wrong_count = 0
        unanswered_count = 0

        for answer_req in req.answers:
            question = self.db.get(Question, answer_req.question_id)
            if not question:
                continue

            # 获取正确答案
            correct_options = self.db.execute(
                select(QuestionOption).where(
                    QuestionOption.question_id == question.id,
                    QuestionOption.is_correct == True
                )
            ).scalars().all()
            correct_keys = {o.option_key for o in correct_options}

            selected = set(answer_req.selected_keys or [])
            is_correct = selected == correct_keys and len(selected) > 0

            if not selected:
                unanswered_count += 1
            elif is_correct:
                correct_count += 1
            else:
                wrong_count += 1

            # 保存答题记录
            answer = UserAnswer(
                exam_record_id=exam.id,
                question_id=question.id,
                selected_options=json.dumps(list(selected)),
                is_correct=is_correct,
                answered_at=datetime.now(timezone.utc),
            )
            self.db.add(answer)

            # 错题自动入错题本
            if not is_correct and selected:
                self._add_to_wrong_book(user_id, question.id)

        # 计算得分 (满分1000分制)
        score = round(
            (correct_count / exam.total_questions) * 1000
        ) if exam.total_questions > 0 else 0
        is_passed = score >= exam.pass_score if exam.pass_score else None

        # 更新考试记录
        exam.correct_count = correct_count
        exam.wrong_count = wrong_count
        exam.unanswered_count = unanswered_count
        exam.score = score
        exam.is_passed = is_passed
        exam.used_seconds = req.used_seconds
        exam.status = "completed"
        exam.completed_at = datetime.now(timezone.utc)

        # 更新学习进度
        self._update_study_progress(
            user_id, exam.certification_id,
            exam.total_questions, correct_count, is_passed or False
        )

        self.db.commit()
        return exam

    def _add_to_wrong_book(self, user_id: int, question_id: int):
        """添加到错题本"""
        wb = self.db.execute(
            select(WrongBook).where(
                WrongBook.user_id == user_id,
                WrongBook.question_id == question_id,
            )
        ).scalar_one_or_none()

        if wb:
            wb.wrong_count += 1
            wb.last_wrong_at = datetime.now(timezone.utc)
            wb.is_mastered = False
        else:
            wb = WrongBook(
                user_id=user_id,
                question_id=question_id,
                wrong_count=1,
                last_wrong_at=datetime.now(timezone.utc),
            )
            self.db.add(wb)

    def _update_study_progress(
        self, user_id: int, certification_id: int,
        total: int, correct: int, passed: bool
    ):
        """更新学习进度"""
        sp = self.db.execute(
            select(StudyProgress).where(
                StudyProgress.user_id == user_id,
                StudyProgress.certification_id == certification_id,
            )
        ).scalar_one_or_none()

        if not sp:
            sp = StudyProgress(
                user_id=user_id,
                certification_id=certification_id,
            )
            self.db.add(sp)

        sp.questions_answered = (sp.questions_answered or 0) + total
        sp.questions_correct = (sp.questions_correct or 0) + correct
        sp.exam_count = (sp.exam_count or 0) + 1
        if passed:
            sp.exam_passed = (sp.exam_passed or 0) + 1
        sp.last_study_at = datetime.now(timezone.utc)
