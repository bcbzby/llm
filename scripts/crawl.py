"""
Crawler CLI script - manage crawlers from command line

Usage:
  python scripts/crawl.py urls --source examtopics URL1 URL2
  python scripts/crawl.py paginated --base-url "https://..." --max-pages 10
  python scripts/crawl.py source --key aws_faq
  python scripts/crawl.py list-sources
  python scripts/crawl.py stats
"""
import sys
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="CloudCert Pro 爬虫管理")
    sub = parser.add_subparsers(dest="command")

    # urls 命令
    urls_p = sub.add_parser("urls", help="从 URL 列表爬取")
    urls_p.add_argument("--source", default="web", help="来源标识")
    urls_p.add_argument("--subject-id", type=int, default=1, help="科目 ID")
    urls_p.add_argument("urls", nargs="+", help="页面 URL")

    # paginated 命令
    pag_p = sub.add_parser("paginated", help="分页爬取")
    pag_p.add_argument("--base-url", required=True, help="基础 URL")
    pag_p.add_argument("--source", default="web", help="来源标识")
    pag_p.add_argument("--subject-id", type=int, default=1, help="科目 ID")
    pag_p.add_argument("--max-pages", type=int, default=50, help="最大页数")
    pag_p.add_argument("--url-template", help="URL 模板，如 https://example.com/q/{}")

    # source 命令
    src_p = sub.add_parser("source", help="爬取预定义来源")
    src_p.add_argument("--key", required=True, help="来源 key（用 list-sources 查看）")
    src_p.add_argument("--subject-id", type=int, default=1, help="科目 ID")

    # list-sources 命令
    sub.add_parser("list-sources", help="列出可用预定义来源")

    # stats 命令
    sub.add_parser("stats", help="查看题库统计")

    args = parser.parse_args()

    # 延迟导入（需要 app 环境）
    sys.path.insert(0, "backend")
    from app.database import SessionLocal
    from app.crawler.service import CrawlerService
    from app.crawler.sources import PREDEFINED_SOURCES
    from app.models.tag import Tag
    from sqlalchemy import select

    db = SessionLocal()
    try:
        if args.command == "urls":
            tags_result = db.execute(select(Tag)).scalars().all()
            tag_map = {t.name: t.id for t in tags_result}
            service = CrawlerService(db)
            result = service.crawl_urls(args.urls, source=args.source, subject_id=args.subject_id, tag_map=tag_map)

        elif args.command == "paginated":
            tags_result = db.execute(select(Tag)).scalars().all()
            tag_map = {t.name: t.id for t in tags_result}
            service = CrawlerService(db)
            result = service.crawl_paginated(
                args.base_url, source=args.source, subject_id=args.subject_id,
                max_pages=args.max_pages, url_template=args.url_template, tag_map=tag_map,
            )

        elif args.command == "source":
            service = CrawlerService(db)
            result = service.crawl_predefined_source(args.key, subject_id=args.subject_id)

        elif args.command == "list-sources":
            print("\n📦 预定义来源:")
            for key, cfg in PREDEFINED_SOURCES.items():
                print(f"  [{key}] {cfg['label']} ({cfg['type']})")
                for url in cfg.get("urls", []):
                    print(f"    └ {url}")
                print()
            return

        elif args.command == "stats":
            from sqlalchemy import func
            from app.models.question import Question
            total = db.execute(select(func.count(Question.id))).scalar() or 0
            verified = db.execute(select(func.count(Question.id)).where(Question.is_verified == True)).scalar() or 0
            by_source = db.execute(
                select(Question.source, func.count(Question.id))
                .where(Question.source.isnot(None))
                .group_by(Question.source)
            ).all()
            print(f"\n📊 题库统计:")
            print(f"  总题目数: {total}")
            print(f"  已验证: {verified}")
            print(f"  按来源:")
            for src, cnt in by_source:
                print(f"    {src or 'manual'}: {cnt}")
            return

        else:
            parser.print_help()
            return

        # 打印导入结果
        print(f"\n✅ 导入完成:")
        print(f"  总计: {result.total}")
        print(f"  新增: {result.imported}")
        print(f"  跳过(重复): {result.skipped}")
        print(f"  失败: {result.failed}")
        if result.errors:
            print(f"  错误信息:")
            for e in result.errors[:5]:
                print(f"    ⚠ {e}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
