#!/usr/bin/env python3
"""
CloudCert Pro - 知识库爬虫脚本
爬取 AWS 官方文档生成知识文章并导入数据库。

用法:
  python scripts/crawl_knowledge.py --all          # 爬取所有来源
  python scripts/crawl_knowledge.py --source ec2   # 爬取指定来源
  python scripts/crawl_knowledge.py --url https://... --category compute  # 爬取单个URL
  python scripts/crawl_knowledge.py --list         # 列出可用来源
  python scripts/crawl_knowledge.py --stats        # 查看知识库统计
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import argparse
from app.database import SessionLocal
from app.crawler.knowledge_crawler import KnowledgeCrawler, KNOWLEDGE_SOURCES
from app.crawler.knowledge_importer import KnowledgeImporter
from app.models.user import User
from app.models.knowledge import KnowledgeArticle
from sqlalchemy import select, func


SOURCE_ALIASES = {
    "ec2": "aws_ec2_guide",
    "s3": "aws_s3_guide",
    "vpc": "aws_vpc_guide",
    "rds": "aws_rds_guide",
    "lambda": "aws_lambda_guide",
    "dynamodb": "aws_dynamodb_guide",
    "iam": "aws_iam_guide",
    "cloudfront": "aws_cloudfront_guide",
    "sagemaker": "aws_sagemaker_guide",
    "elb": "aws_elb_guide",
    "ecs": "aws_ecs_guide",
}


def main():
    parser = argparse.ArgumentParser(description="CloudCert Pro - 知识库爬虫")
    parser.add_argument("--all", action="store_true", help="爬取所有来源")
    parser.add_argument("--source", type=str, help="爬取指定来源 (ec2/s3/vpc/rds/lambda/dynamodb/iam/cloudfront/sagemaker/elb/ecs)")
    parser.add_argument("--url", type=str, help="爬取单个URL")
    parser.add_argument("--category", type=str, default="general", help="URL的分类")
    parser.add_argument("--list", action="store_true", help="列出可用来源")
    parser.add_argument("--stats", action="store_true", help="查看知识库统计")
    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        return

    if args.list:
        print("\n📚 可用爬取来源:\n")
        for key, cfg in KNOWLEDGE_SOURCES.items():
            alias = [k for k, v in SOURCE_ALIASES.items() if v == key]
            alias_str = f" (alias: {alias[0]})" if alias else ""
            print(f"  [{key}]{alias_str}")
            print(f"    名称: {cfg['label']}")
            print(f"    分类: {cfg['category']}")
            print(f"    标签: {', '.join(cfg['tags'])}")
            for url in cfg['urls']:
                print(f"    URL: {url}")
            print()
        return

    db = SessionLocal()
    try:
        admin = db.execute(select(User).where(User.email == "admin@cloudcert.com")).scalar_one()
        importer = KnowledgeImporter(db, created_by=admin.id)
        crawler = KnowledgeCrawler()

        if args.stats:
            total = db.execute(select(func.count(KnowledgeArticle.id))).scalar() or 0
            by_cat = db.execute(
                select(KnowledgeArticle.category, func.count(KnowledgeArticle.id))
                .group_by(KnowledgeArticle.category)
            ).all()
            print(f"\n📊 知识库统计: 共 {total} 篇文章\n")
            for cat, cnt in by_cat:
                print(f"  {cat}: {cnt} 篇")
            return

        if args.url:
            print(f"正在爬取: {args.url}")
            article = crawler.crawl_url(args.url, category=args.category)
            if article:
                result = importer.import_articles([article])
                print(f"  导入: {result.imported} 篇, 跳过: {result.skipped}")
            else:
                print("  ❌ 爬取失败")
            return

        if args.all:
            print("正在爬取所有来源...")
            articles = crawler.crawl_all()
            print(f"  共爬取 {len(articles)} 篇文章")
            result = importer.import_articles(articles)
            print(f"\n✅ 导入结果:")
            print(f"  新增: {result.imported}")
            print(f"  跳过(重复): {result.skipped}")
            print(f"  失败: {result.failed}")
            return

        if args.source:
            source_key = SOURCE_ALIASES.get(args.source, args.source)
            print(f"正在爬取: {source_key}")
            articles = crawler.crawl_source(source_key)
            print(f"  共爬取 {len(articles)} 篇文章")
            result = importer.import_articles(articles)
            print(f"\n✅ 导入结果:")
            print(f"  新增: {result.imported}")
            print(f"  跳过(重复): {result.skipped}")
            return

    finally:
        db.close()


if __name__ == "__main__":
    main()
