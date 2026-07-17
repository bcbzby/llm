from sqlalchemy import select
from sqlalchemy.orm import Session
import json

from app.models.exam import ExamRecord, UserAnswer
from app.models.question import Question, QuestionOption, QuestionTag
from app.models.tag import Tag
from app.models.certification import Subject
from app.services.scoring_service import ScoringService


class ReportService:
    """报告生成服务"""

    def __init__(self, db: Session):
        self.db = db
        self.scoring = ScoringService()

    def get_exam_report(self, exam_id: int):
        """获取考试评估报告"""
        exam = self.db.get(ExamRecord, exam_id)
        if not exam:
            raise ValueError("考试不存在")

        # 获取答题记录
        answers = list(self.db.execute(
            select(UserAnswer).where(UserAnswer.exam_record_id == exam_id)
        ).scalars().all())

        # 获取题目信息
        questions_map = {}
        for answer in answers:
            q = self.db.get(Question, answer.question_id)
            if q:
                q.options = list(self.db.execute(
                    select(QuestionOption).where(QuestionOption.question_id == q.id)
                ).scalars().all())
                questions_map[q.id] = q

        return self.scoring.generate_report(exam, answers, questions_map)

    def get_exam_result(self, exam_id: int):
        """获取考试结果详情（含每题对错）"""
        exam = self.db.get(ExamRecord, exam_id)
        if not exam:
            raise ValueError("考试不存在")

        answers = list(self.db.execute(
            select(UserAnswer).where(UserAnswer.exam_record_id == exam_id)
        ).scalars().all())

        question_results = []
        for answer in answers:
            question = self.db.get(Question, answer.question_id)
            if not question:
                continue

            all_options = list(self.db.execute(
                select(QuestionOption).where(QuestionOption.question_id == question.id)
            ).scalars().all())
            correct_keys = sorted([o.option_key for o in all_options if o.is_correct])

            question_results.append({
                "question_id": question.id,
                "content": question.content,
                "question_type": question.question_type,
                "options": [
                    {"key": o.option_key, "content": o.content}
                    for o in all_options
                ],
                "selected_keys": sorted(json.loads(answer.selected_options)) if answer.selected_options else [],
                "correct_keys": correct_keys,
                "is_correct": answer.is_correct,
                "explanation": question.explanation,
            })

        gap_to_pass = max(0, (exam.pass_score or 0) - exam.score) if not exam.is_passed else 0

        return {
            "exam_id": exam.id,
            "title": exam.title,
            "status": exam.status,
            "total_questions": exam.total_questions,
            "correct_count": exam.correct_count,
            "wrong_count": exam.wrong_count,
            "unanswered_count": exam.unanswered_count,
            "score": exam.score,
            "total_score": exam.total_score,
            "pass_score": exam.pass_score,
            "is_passed": exam.is_passed,
            "gap_to_pass": gap_to_pass,
            "used_seconds": exam.used_seconds,
            "duration_min": exam.duration_min,
            "started_at": exam.started_at,
            "completed_at": exam.completed_at,
            "question_results": question_results,
        }
