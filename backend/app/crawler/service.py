"""
Crawler orchestration service - manages crawl, parse, import pipeline
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.crawler.sources import (
    CrawlerClient, URLListCrawler, PaginatedCrawler,
    AWSFAQCrawler, CrawlResult, PREDEFINED_SOURCES,
)
from app.crawler.importer import QuestionImporter, BulkImportResult

logger = logging.getLogger(__name__)


class CrawlerService:
    """爬虫编排服务"""

    def __init__(self, db: Session, user_id: Optional[int] = None):
        self.db = db
        self.user_id = user_id

    def crawl_urls(
        self,
        urls: list[str],
        source: str = "web",
        subject_id: int = 1,
        tag_map: Optional[dict] = None,
    ) -> BulkImportResult:
        """单步：从 URLs 爬取 → 解析 → 导入

        Args:
            urls: 要爬取的页面 URL 列表
            source: 来源标识
            subject_id: 导入到哪个科目下
            tag_map: 标签名 -> ID 映射
        """
        client = CrawlerClient(base_delay=2.0, jitter=1.0)

        # 1. 爬取
        crawler = URLListCrawler(client)
        results = crawler.crawl_urls(urls, source=source)

        # 2. 合并解析结果
        all_questions = []
        total_pages = 0
        for r in results:
            all_questions.extend(r.questions)
            total_pages += 1

        # 3. 导入数据库
        importer = QuestionImporter(self.db, default_subject_id=subject_id, created_by=self.user_id)
        import_result = importer.import_parsed(all_questions, tag_map=tag_map)

        return import_result

    def crawl_paginated(
        self,
        base_url: str,
        source: str = "web",
        subject_id: int = 1,
        max_pages: int = 50,
        url_template: Optional[str] = None,
        tag_map: Optional[dict] = None,
    ) -> BulkImportResult:
        """分页爬取 → 解析 → 导入"""
        client = CrawlerClient(base_delay=3.0, jitter=1.5)
        crawler = PaginatedCrawler(client)
        result = crawler.crawl(base_url, source=source, max_pages=max_pages, url_template=url_template)

        importer = QuestionImporter(self.db, default_subject_id=subject_id, created_by=self.user_id)
        import_result = importer.import_parsed(result.questions, tag_map=tag_map)

        return import_result

    def crawl_faq(
        self,
        url: str,
        source: str = "aws_faq",
        subject_id: int = 1,
    ) -> BulkImportResult:
        """爬取 FAQ 页面"""
        client = CrawlerClient(base_delay=1.0, jitter=0.5)
        crawler = AWSFAQCrawler(client)
        result = crawler.crawl_faq(url, source=source)

        importer = QuestionImporter(self.db, default_subject_id=subject_id, created_by=self.user_id)
        import_result = importer.import_parsed(result.questions)

        return import_result

    def crawl_predefined_source(
        self,
        source_key: str,
        subject_id: int = 1,
    ) -> BulkImportResult:
        """爬取预定义来源"""
        if source_key not in PREDEFINED_SOURCES:
            raise ValueError(f"未知来源: {source_key}，可用: {list(PREDEFINED_SOURCES.keys())}")

        config = PREDEFINED_SOURCES[source_key]
        source_type = config["type"]

        if source_type == "url_list":
            return self.crawl_urls(config["urls"], source=source_key, subject_id=subject_id)
        elif source_type == "faq":
            # FAQ: 逐个爬取
            client = CrawlerClient(base_delay=1.0, jitter=0.5)
            crawler = AWSFAQCrawler(client)
            all_questions = []
            for url in config["urls"]:
                r = crawler.crawl_faq(url, source=source_key)
                all_questions.extend(r.questions)

            importer = QuestionImporter(self.db, default_subject_id=subject_id, created_by=self.user_id)
            return importer.import_parsed(all_questions)
        else:
            raise ValueError(f"不支持的类型: {source_type}")
