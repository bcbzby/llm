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
    """构造 3 个认证，含跨认证内容重复（模拟实际种子数据）
    - cert_zh: 5 道中文题（前 3 道与 cert_b 共享内容）
    - cert_mixed: 3 道中文题 + 10 道英文题
    - cert_b: 3 道中文题（与 cert_zh 共享内容）
    """
    cert_zh = Certification(provider="aws", code="aws-zh", name="ZH Cert", level="associate",
                            total_questions=65, pass_score=720, duration_min=130, is_active=True)
    cert_mixed = Certification(provider="aws", code="aws-clf", name="Cloud Practitioner", level="foundational",
                               total_questions=65, pass_score=700, duration_min=90, is_active=True)
    cert_b = Certification(provider="aws", code="aws-shared", name="Shared", level="associate",
                           total_questions=65, pass_score=720, duration_min=130, is_active=True)
    db.add_all([cert_zh, cert_mixed, cert_b])
    db.flush()

    subj_zh = Subject(certification_id=cert_zh.id, name="ZH科目", sort_order=1, weight=100)
    subj_mixed = Subject(certification_id=cert_mixed.id, name="Mixed Subject", sort_order=1, weight=100)
    subj_b = Subject(certification_id=cert_b.id, name="Shared Subj", sort_order=1, weight=100)
    db.add_all([subj_zh, subj_mixed, subj_b])
    db.flush()

    shared = ["共享题目A？", "共享题目B？", "共享题目C？"]

    # cert_zh: 5 道中文题（前 3 道共享）
    for i, content in enumerate(shared + ["独立题X？", "独立题Y？"]):
        q = Question(subject_id=subj_zh.id, question_type="single_choice", difficulty="medium",
                     content=content, status="published", is_verified=True)
        db.add(q)
        db.flush()
        db.add(QuestionOption(question_id=q.id, option_key="A", content="OptA", is_correct=True, sort_order=0))
        db.add(QuestionOption(question_id=q.id, option_key="B", content="OptB", is_correct=False, sort_order=1))

    # cert_b: 3 道共享中文题（与 cert_zh 内容相同）
    for content in shared:
        q = Question(subject_id=subj_b.id, question_type="single_choice", difficulty="medium",
                     content=content, status="published", is_verified=True)
        db.add(q)
        db.flush()
        db.add(QuestionOption(question_id=q.id, option_key="A", content="OptA", is_correct=True, sort_order=0))
        db.add(QuestionOption(question_id=q.id, option_key="B", content="OptB", is_correct=False, sort_order=1))

    # cert_mixed: 3 中文 + 10 英文
    for i in range(3):
        q = Question(subject_id=subj_mixed.id, question_type="single_choice", difficulty="medium",
                     content=f"混合中文题 {i}？", status="published", is_verified=True)
        db.add(q)
        db.flush()
        db.add(QuestionOption(question_id=q.id, option_key="A", content="是", is_correct=True, sort_order=0))
        db.add(QuestionOption(question_id=q.id, option_key="B", content="否", is_correct=False, sort_order=1))
    for i in range(10):
        q = Question(subject_id=subj_mixed.id, question_type="single_choice", difficulty="medium",
                     content=f"English Q{i}?", status="published", is_verified=True)
        db.add(q)
        db.flush()
        db.add(QuestionOption(question_id=q.id, option_key="A", content="T", is_correct=True, sort_order=0))
        db.add(QuestionOption(question_id=q.id, option_key="B", content="F", is_correct=False, sort_order=1))

    db.commit()
    return cert_zh.id, cert_mixed.id, cert_b.id


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
                                  random_sample=True, page_size=5)
        assert len(data["items"]) == 5, f"应抽到5题，实际 {len(data['items'])}"
        ids = [it["id"] for it in data["items"]]
        assert len(set(ids)) == 5, "单次抽取内部出现重复题目"
        seen.update(ids)

    # 5 个唯一中文题（3共享+2独立），多次抽取应全部覆盖
    assert len(seen) == 5, f"随机抽题未覆盖全部唯一内容，仅命中 {len(seen)}/5"
    assert data["total"] == 5, f"total 应为去重后总数 5，实际 {data['total']}"
    print(f"[PASS] Bug1 随机抽题覆盖全量：去重后5个唯一题全部命中")
    db.close()


def test_exclude_ids_avoids_repeats(cert_zh_id):
    """Bug1: 传入 exclude_ids 后，抽到的题不应包含已排除的题"""
    db = _make_session()
    _seed(db)
    svc = QuestionService(db)

    first = svc.get_questions(certification_id=cert_zh_id, lang="zh",
                              random_sample=True, page_size=5)
    used_ids = [it["id"] for it in first["items"]]

    second = svc.get_questions(certification_id=cert_zh_id, lang="zh",
                               random_sample=True, page_size=5,
                               exclude_ids=",".join(map(str, used_ids)))
    second_ids = {it["id"] for it in second["items"]}

    assert not (set(used_ids) & second_ids), "排除后仍出现重复题目"
    print("[PASS] Bug1 exclude_ids 成功避免重复")
    db.close()


def test_mixed_cert_returns_full_count(cert_mixed_id):
    """Bug2: 对英文题为主的认证，选英文语言应能取满所需题量"""
    db = _make_session()
    _seed(db)
    svc = QuestionService(db)

    # 选 8 道英文题：该认证有 10 道英文题，应取满
    data = svc.get_questions(certification_id=cert_mixed_id, lang="en",
                             random_sample=True, page_size=8)
    assert len(data["items"]) == 8, f"英文题应取满8道，实际 {len(data['items'])}"
    for it in data["items"]:
        assert not _has_chinese(it["content"]), "en 过滤后混入了中文题"
    print(f"[PASS] Bug2 混合认证英文抽题取满：{len(data['items'])}/8，total={data['total']}")

    # 选 5 道中文题：该认证只有 3 道中文题，应返回 3 道（不报错、不混英文）
    data_zh = svc.get_questions(certification_id=cert_mixed_id, lang="zh",
                                random_sample=True, page_size=5)
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
                             page=1, page_size=8)
    assert data["total"] == 10, f"英文题总数应为10，实际 {data['total']}"
    assert len(data["items"]) == 8, "分页大小不对"
    for it in data["items"]:
        assert not _has_chinese(it["content"])
    print(f"[PASS] 非随机模式语言过滤+分页正确：total={data['total']}，本页={len(data['items'])}")
    db.close()


def test_random_sample_deduplicates_content(cert_zh_id, cert_b_id):
    """核心测试：跨认证存在重复内容时，random_sample 模式必须按内容去重"""
    db = _make_session()
    _seed(db)
    svc = QuestionService(db)

    # cert_zh: 5 行 DB 记录（3共享+2独立）→ 5 唯一内容
    for _ in range(5):
        data = svc.get_questions(certification_id=cert_zh_id, lang="zh",
                                 random_sample=True, page_size=5)
        assert len(data["items"]) == 5, f"应去重后抽到5题，实际 {len(data['items'])}"
        assert len(set(it["content"] for it in data["items"])) == 5, "去重失败：有内容重复"
    print(f"[PASS] 去重 test: cert_zh 有 {data['total']} 唯一内容")

    # 不加 cert 抽查全部中文题：cert_zh(5) + cert_b(3共享) + cert_mixed(3) = 11 DB 行
    # 去重后: 3 共享 ✓ + 2 独立 ✓ + 3 混合 ✓ = 8 唯一内容
    data_all = svc.get_questions(lang="zh", random_sample=True, page_size=10)
    assert data_all["total"] == 8, f"全部中文去重后应为8个唯一内容，实际 {data_all['total']}"
    assert len(data_all["items"]) == 8
    contents = [it["content"] for it in data_all["items"]]
    assert len(set(contents)) == 8, "全部题库去重后仍有重复内容"
    print(f"[PASS] 全部题库去重准确：{data_all['total']}/8 唯一内容")

    db.close()


def run_all():
    db = _make_session()
    cert_zh_id, cert_mixed_id, cert_b_id = _seed(db)
    db.close()

    test_has_chinese()
    test_random_sample_covers_full_bank(cert_zh_id)
    test_exclude_ids_avoids_repeats(cert_zh_id)
    test_mixed_cert_returns_full_count(cert_mixed_id)
    test_lang_filter_pagination(cert_mixed_id)
    test_random_sample_deduplicates_content(cert_zh_id, cert_b_id)
    print("\n=== All tests passed ===")


if __name__ == "__main__":
    run_all()
