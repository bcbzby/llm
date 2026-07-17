from dataclasses import dataclass
from typing import Dict


@dataclass
class TagStat:
    """单标签统计"""
    tag_id: int
    tag_name: str
    total: int = 0
    correct: int = 0

    @property
    def correct_rate(self) -> float:
        return round(self.correct / self.total * 100, 1) if self.total else 0.0


@dataclass
class SubjectStat:
    """科目统计"""
    subject_id: int
    subject_name: str
    weight: float
    total: int = 0
    correct: int = 0

    @property
    def correct_rate(self) -> float:
        return round(self.correct / self.total * 100, 1) if self.total else 0.0


class ScoringService:
    """评分与报告生成引擎"""

    def generate_report(self, exam, answers, questions_map):
        """
        生成完整评估报告

        Args:
            exam: ExamRecord 对象
            answers: List[UserAnswer]
            questions_map: Dict[int, Question] 题目查询映射
        """
        tag_stats: Dict[int, TagStat] = {}
        subject_stats: Dict[int, SubjectStat] = {}

        for answer in answers:
            question = questions_map.get(answer.question_id)
            if not question:
                continue

            # 按标签统计
            if hasattr(question, 'tags') and question.tags:
                for qt in question.tags:
                    if hasattr(qt, 'tag_id'):
                        tid = qt.tag_id
                        tname = getattr(qt, 'tag_name', str(tid))
                        if tid not in tag_stats:
                            tag_stats[tid] = TagStat(tag_id=tid, tag_name=tname)
                        tag_stats[tid].total += 1
                        if answer.is_correct:
                            tag_stats[tid].correct += 1

            # 按科目统计
            if hasattr(question, 'subject') and question.subject:
                subject = question.subject
                sid = subject.id
                if sid not in subject_stats:
                    subject_stats[sid] = SubjectStat(
                        subject_id=sid,
                        subject_name=subject.name,
                        weight=getattr(subject, 'weight', 0) or 0,
                    )
                subject_stats[sid].total += 1
                if answer.is_correct:
                    subject_stats[sid].correct += 1

        # 分析薄弱/优势知识点
        weakness = sorted(
            [s for s in tag_stats.values() if s.total >= 2],
            key=lambda x: x.correct_rate
        )[:5]

        strength = sorted(
            [s for s in tag_stats.values() if s.total >= 2],
            key=lambda x: -x.correct_rate
        )[:5]

        correct_rate_str = (
            f"{exam.correct_count / exam.total_questions * 100:.1f}%"
            if exam.total_questions > 0 else "0.0%"
        )

        return {
            "exam_summary": {
                "exam_id": exam.id,
                "title": exam.title,
                "score": exam.score,
                "total_score": exam.total_score,
                "correct_rate": correct_rate_str,
                "is_passed": exam.is_passed,
                "gap_to_pass": max(0, (exam.pass_score or 0) - exam.score) if not exam.is_passed else 0,
            },
            "subject_breakdown": sorted(
                [
                    {
                        "subject_id": s.subject_id,
                        "subject_name": s.subject_name,
                        "weight": float(s.weight),
                        "total": s.total,
                        "correct": s.correct,
                        "correct_rate": f"{s.correct_rate}%",
                    }
                    for s in subject_stats.values()
                ],
                key=lambda x: x["subject_id"]
            ),
            "tag_breakdown": sorted(
                [
                    {
                        "tag_id": t.tag_id,
                        "tag_name": t.tag_name,
                        "total": t.total,
                        "correct": t.correct,
                        "correct_rate": f"{t.correct_rate}%",
                    }
                    for t in tag_stats.values()
                ],
                key=lambda x: x["tag_id"]
            ),
            "weakness_tags": [
                {
                    "tag_id": t.tag_id, "tag_name": t.tag_name,
                    "correct_rate": f"{t.correct_rate}%",
                    "suggested_action": f"建议复习 {t.tag_name} 相关章节",
                }
                for t in weakness
            ],
            "strength_tags": [
                {
                    "tag_id": t.tag_id, "tag_name": t.tag_name,
                    "correct_rate": f"{t.correct_rate}%",
                    "suggested_action": "保持复习节奏",
                }
                for t in strength
            ],
        }
