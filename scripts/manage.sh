#!/bin/bash
# CloudCert Pro - 一键管理脚本
# 用法: bash manage.sh [命令]
#
# 命令:
#   seed       - 初始化/重新分配题库和知识库
#   crawl      - 爬取 AWS 官方 FAQ
#   generate   - 从模板生成更多题目
#   all        - 完整更新（爬虫+生成+分配）
#   stats      - 查看题库统计
#   reset      - 清空所有数据并重新导入
#
# 示例:
#   bash manage.sh all     # 一键更新所有
#   bash manage.sh stats   # 查看统计

set -e

PROJECT=/opt/cloudcert-pro
COMPOSE="docker compose -f ${PROJECT}/docker-compose.prod.yml"

echo "========================================"
echo "  CloudCert Pro - 管理脚本"
echo "========================================"

case "${1:-stats}" in
  seed)
    echo "[任务] 初始化/重新分配题库和知识库..."
    $COMPOSE exec backend sh -c "cd /app && PYTHONPATH=/app python /app/scripts/seed_data.py"
    $COMPOSE exec backend sh -c "cd /app && PYTHONPATH=/app python /app/scripts/generate_knowledge.py --all 2>/dev/null || true"
    echo "[完成]"
    ;;

  crawl)
    echo "[任务] 爬取 AWS 官方 FAQ..."
    for source in aws_ec2_faq aws_s3_faq aws_vpc_faq aws_rds_faq aws_lambda_faq; do
      echo "  爬取 $source ..."
      $COMPOSE exec backend sh -c "cd /app && PYTHONPATH=/app python /app/scripts/crawl.py source --key $source --subject-id 1" 2>/dev/null || true
    done
    echo "[完成]"
    ;;

  crawl-knowledge)
    echo "[任务] 爬取 AWS 官方文档(知识库)..."
    $COMPOSE exec backend sh -c "cd /app && PYTHONPATH=/app python /app/scripts/crawl_knowledge.py --all" 2>/dev/null || true
    echo "[完成]"
    ;;

  generate)
    echo "[任务] 从模板生成题目..."
    $COMPOSE exec backend sh -c "cd /app && PYTHONPATH=/app python /app/scripts/generate_questions.py --generate 30" 2>/dev/null || true
    echo "[完成]"
    ;;

  all)
    echo "[任务] 完整更新（爬虫+生成+知识库+分配）..."
    bash "$0" crawl
    bash "$0" crawl-knowledge
    bash "$0" generate
    bash "$0" seed
    echo ""
    echo "所有任务完成！访问 http://10.60.79.158:5173 查看"
    ;;

  stats)
    echo "[任务] 题库统计..."
    $COMPOSE exec backend sh -c "
      cd /app && PYTHONPATH=/app python -c \"
import sys; sys.path.insert(0, '/app')
from app.database import SessionLocal
from app.models.certification import Certification, Subject
from app.models.question import Question
from app.models.knowledge import KnowledgeArticle
from sqlalchemy import select, func
db = SessionLocal()
certs = list(db.execute(select(Certification)).scalars().all())
for c in certs:
    sub_ids = [s.id for s in db.execute(select(Subject).where(Subject.certification_id == c.id)).scalars().all()]
    cnt = db.execute(select(func.count(Question.id)).where(Question.subject_id.in_(sub_ids))).scalar() or 0
    status = 'OK' if cnt >= c.total_questions else 'SHORT'
    pct = min(100, int(cnt * 100 / max(c.total_questions, 1)))
    print(f'  [{status}] {c.code:12s} {cnt:3d}/{c.total_questions} ({pct:2d}%)')
total_q = db.execute(select(func.count(Question.id))).scalar() or 0
total_k = db.execute(select(func.count(KnowledgeArticle.id))).scalar() or 0
print(f'')
print(f'  Total questions: {total_q}')
print(f'  Knowledge articles: {total_k}')
db.close()
\""
    ;;

  reset)
    echo "[任务] 清空所有数据并重新导入..."
    echo "  WARNING: 这将删除所有题目、知识库和用户数据！"
    read -p "  确认继续? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
      $COMPOSE exec backend sh -c "cd /app && PYTHONPATH=/app python /app/scripts/seed_data.py --clear"
      bash "$0" all
    else
      echo "  已取消"
    fi
    ;;

  *)
    echo "用法: bash manage.sh [命令]"
    echo ""
    echo "命令:"
    echo "  seed       - 初始化/重新分配题库和知识库"
    echo "  crawl      - 爬取 AWS 官方 FAQ"
    echo "  generate   - 从模板生成更多题目"
    echo "  all        - 完整更新（爬虫+生成+分配）"
    echo "  stats      - 查看题库统计"
    echo "  reset      - 清空所有数据并重新导入"
    ;;
esac
