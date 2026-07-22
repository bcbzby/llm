# -*- coding: utf-8 -*-
"""
QuestionService 单元测试 —— 针对刷题功能两个 bug 的回归测试：

Bug 1: 刷题出现题目重复（后端未随机抽题，总是返回最新一页，前端只能在固定池里洗牌）
Bug 2: 选择某些认证（如 aws-clf / aws-dop）时题目达不到所选数量（前端在最多100条里再按语言过滤，
       中文题极少，导致只剩几道题）

修复方案：随机抽题、语言过滤、排除已出题目全部下沉到后端的 QuestionService.get_questions，
基于整个题库而非最新一页。

运行方式（无需 pytest，也可 pytest）：
    python tests/test_question_service.py
"""
import os
import sys

# 保证可导入 app 包
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 提供测试所需的最小环境变量（config 需要这些必填项）
os.environ.setdefault("APP_SECRET_KEY", "test-secret")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
# app.database 在导入时会用该 URL 建立模块级 engine；用临时文件库避免 in-memory
# 触发 SingletonThreadPool 不接受 pool_size/max_overflow 的问题。测试自身另建 engine。
os.environ.setdefault("DATABASE_URL", "sqlite:///./_pytest_tmp.db")
os.environ.setdefault("APP_DEBUG", "false")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
# 注册所有模型到 Base.metadata
from app.models.certification import Certification, Subject  # noqa: F401
from app.models.question import Question, QuestionOption, QuestionTag  # noqa: F401
from app.models.tag import Tag  # noqa: F401
from app.services.question_service import QuestionService, _has_chinese


def _make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(engine, expire_on_commit=False)()


def _seed(db):
    """构造两个认证：
    - cert_zh (id=1): 30 道中文题
    - cert_mixed (id=2): 3 道中文题 + 40 道英文题（模拟 aws-clf/aws-dop 的分布）
    """
    cert_zh = Certification(provider="aws", code="aws-zh", name="ZH Cert", level="associate",
                            total_questions=65, pass_score=720, duration_min=130, is_active=True)
    cert_mixed = Certification(provider="aws", code="aws-clf", name="Cloud Practitioner", level="foundational",
                               total_questions=65, pass_score=700, duration_min=90, is_active=True)
    db.add_all([cert_zh, cert_mixed])
    db.flush()

    subj_zh = Subject(certification_id=cert_zh.id, name="ZH科目", sort_order=1, weight=100)
    subj_mixed = Subject(certification_id=cert_mixed.id, name="Mixed Subject", sort_order=1, weight=100)
    db.add_all([subj_zh, subj_mixed])
    db.flush()

    # cert_zh: 30 道中文题
    for i in range(30):
        q = Question(subject_id=subj_zh.id, question_type="single_choice", difficulty="medium",
                     content=f"这是第 {i} 道中文题目？", status="published", is_verified=True)
        db.add(q)
        db.flush()
        db.add(QuestionOption(question_id=q.id, option_key="A", content="选项A", is_correct=True, sort_order=0))
        db.add(QuestionOption(question_id=q.id, option_key="B", content="选项B", is_correct=False, sort_order=1))

    # cert_mixed: 3 道中文题 + 40 道英文题
    for i in range(3):
        q = Question(subject_id=subj_mixed.id, question_type="single_choice", difficulty="medium",
                     content=f"混合认证的中文题 {i}？", status="published", is_verified=True)
        db.add(q)
        db.flush()
        db.add(QuestionOption(question_id=q.id, option_key="A", content="是", is_correct=True, sort_order=0))
        db.add(QuestionOption(question_id=q.id, option_key="B", content="否", is_correct=False, sort_order=1))
    for i in range(40):
        q = Question(subject_id=subj_mixed.id, question_type="single_choice", difficulty="medium",
                     content=f"English question number {i}?", status="published", is_verified=True)
        db.add(q)
        db.flush()
        db.add(QuestionOption(question_id=q.id, option_key="A", content="True", is_correct=True, sort_order=0))
        db.add(QuestionOption(question_id=q.id, option_key="B", content="False", is_correct=False, sort_order=1))

    db.commit()
    return cert_zh.id, cert_mixed.id


def test_has_chinese():
    assert _has_chinese("你好 world") is True
    assert _has_chinese("hello world") is False
    assert _has_chinese("") is False
    print("[PASS] _has_chinese 正确识别中英文")


def test_random_sample_covers_full_bank(cert_zh_id):
    """Bug1: 随机抽题应覆盖整个题库，多次抽取应命中不同的题（而不是固定的最新一页）"""
    db = _make_session()
    _seed(db)
    svc = QuestionService(db)

    seen = set()
    for _ in range(20):
        data = svc.get_questions(certification_id=cert_zh_id, lang="zh",
                                  random_sample=True, page_size=10)
        assert len(data["items"]) == 10, f"应抽到10题，实际 {len(data['items'])}"
        # 同一次抽取内不允许重复
        ids = [it["id"] for it in data["items"]]
        assert len(set(ids)) == 10, "单次抽取内部出现重复题目"
        seen.update(ids)

    # 30 道题库，20 次各抽 10 题，应覆盖到远多于 10 道不同题目
    assert len(seen) > 10, f"随机抽题未覆盖整个题库，仅命中 {len(seen)} 道"
    assert data["total"] == 30, f"total 应为题库总数 30，实际 {data['total']}"
    print(f"[PASS] Bug1 随机抽题覆盖题库：20次抽取共命中 {len(seen)}/30 道不同题目")
    db.close()


def test_exclude_ids_avoids_repeats(cert_zh_id):
    """Bug1: 传入 exclude_ids 后，抽到的题不应包含已排除的题"""
    db = _make_session()
    _seed(db)
    svc = QuestionService(db)

    first = svc.get_questions(certification_id=cert_zh_id, lang="zh",
                              random_sample=True, page_size=10)
    used_ids = [it["id"] for it in first["items"]]

    second = svc.get_questions(certification_id=cert_zh_id, lang="zh",
                               random_sample=True, page_size=10,
                               exclude_ids=",".join(map(str, used_ids)))
    second_ids = {it["id"] for it in second["items"]}

    assert not (set(used_ids) & second_ids), "排除后仍出现重复题目"
    assert len(second["items"]) == 10, "排除后题量不足"
    print("[PASS] Bug1 exclude_ids 成功避免重复")
    db.close()


def test_mixed_cert_returns_full_count(cert_mixed_id):
    """Bug2: 对英文题为主的认证，选英文语言应能取满所需题量"""
    db = _make_session()
    _seed(db)
    svc = QuestionService(db)

    # 选 20 道英文题：该认证有 40 道英文题，应取满
    data = svc.get_questions(certification_id=cert_mixed_id, lang="en",
                             random_sample=True, page_size=20)
    assert len(data["items"]) == 20, f"英文题应取满20道，实际 {len(data['items'])}"
    for it in data["items"]:
        assert not _has_chinese(it["content"]), "en 过滤后混入了中文题"
    print(f"[PASS] Bug2 混合认证英文抽题取满：{len(data['items'])}/20，total={data['total']}")

    # 选 20 道中文题：该认证只有 3 道中文题，应返回 3 道（不报错、不混英文）
    data_zh = svc.get_questions(certification_id=cert_mixed_id, lang="zh",
                                random_sample=True, page_size=20)
    assert len(data_zh["items"]) == 3, f"中文题只有3道，应返回3道，实际 {len(data_zh['items'])}"
    for it in data_zh["items"]:
        assert _has_chinese(it["content"]), "zh 过滤后混入了英文题"
    print(f"[PASS] Bug2 中文题不足时安全返回全部：{len(data_zh['items'])}/3，total={data_zh['total']}")
    db.close()


def test_lang_filter_pagination(cert_mixed_id):
    """非随机模式下 lang 过滤 + 分页仍正确"""
    db = _make_session()
    _seed(db)
    svc = QuestionService(db)

    data = svc.get_questions(certification_id=cert_mixed_id, lang="en",
                             page=1, page_size=15)
    assert data["total"] == 40, f"英文题总数应为40，实际 {data['total']}"
    assert len(data["items"]) == 15, "分页大小不对"
    for it in data["items"]:
        assert not _has_chinese(it["content"])
    print(f"[PASS] 非随机模式语言过滤+分页正确：total={data['total']}，本页={len(data['items'])}")
    db.close()


def run_all():
    db = _make_session()
    cert_zh_id, cert_mixed_id = _seed(db)
    db.close()

    test_has_chinese()
    test_random_sample_covers_full_bank(cert_zh_id)
    test_exclude_ids_avoids_repeats(cert_zh_id)
    test_mixed_cert_returns_full_count(cert_mixed_id)
    test_lang_filter_pagination(cert_mixed_id)
    print("\n=== All tests passed ===")


if __name__ == "__main__":
    run_all()
