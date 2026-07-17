"""
Multi-source crawlers - connect to different websites to extract questions

Each source has a CrawlerWorker that supports URL crawling and auto-pagination.
"""
import re
import json
import logging
from urllib.parse import urljoin
from typing import Generator, Optional

from bs4 import BeautifulSoup

from app.crawler import CrawlerClient
from app.crawler.parser import ParsedQuestion, parser_registry

logger = logging.getLogger(__name__)


class CrawlResult:
    """单次爬取结果"""
    def __init__(self, source: str, url: str):
        self.source = source
        self.url = url
        self.questions: list[ParsedQuestion] = []
        self.success = False
        self.error: Optional[str] = None
        self.total_pages = 0


class URLListCrawler:
    """通用 URL 列表爬虫 - 从指定的 URL 列表中逐页抓取"""

    def __init__(self, client: Optional[CrawlerClient] = None):
        self.client = client or CrawlerClient(base_delay=2.5, jitter=1.0)

    def crawl_urls(self, urls: list[str], source: str = "web") -> list[CrawlResult]:
        """从多个 URL 抓取题目"""
        results = []
        for url in urls:
            result = self._crawl_single(url, source)
            results.append(result)
        return results

    def _crawl_single(self, url: str, source: str) -> CrawlResult:
        result = CrawlResult(source=source, url=url)
        try:
            resp = self.client.get(url)
            questions = parser_registry.parse(resp.text, url)
            for q in questions:
                q.source = source
            result.questions = questions
            result.success = True
            logger.info(f"Crawled {len(questions)} questions from {url}")
        except Exception as e:
            result.error = str(e)
            logger.error(f"Failed to crawl {url}: {e}")
        return result


class PaginatedCrawler:
    """支持分页的爬虫 - 自动遍历页面 1..N"""

    def __init__(self, client: Optional[CrawlerClient] = None):
        self.client = client or CrawlerClient(base_delay=3.0, jitter=1.5)

    def crawl(
        self,
        base_url: str,
        source: str,
        max_pages: int = 50,
        page_param: str = "page",
        start_page: int = 1,
        url_template: Optional[str] = None,
    ) -> CrawlResult:
        """爬取分页数据

        Args:
            base_url: 基础 URL
            source: 来源标识
            max_pages: 最大爬取页数
            page_param: URL 中的分页参数名
            start_page: 起始页码
            url_template: 自定义 URL 模板，如 "https://example.com/questions/page/{}"
        """
        result = CrawlResult(source=source, url=base_url)

        for page in range(start_page, start_page + max_pages):
            if url_template:
                page_url = url_template.format(page)
            elif "?" in base_url:
                page_url = f"{base_url}&{page_param}={page}"
            else:
                page_url = f"{base_url}?{page_param}={page}"

            try:
                resp = self.client.get(page_url)
                questions = parser_registry.parse(resp.text, page_url)
                for q in questions:
                    q.source = source
                result.questions.extend(questions)
                result.total_pages += 1

                # 检查是否有下一页（没有分页导航或当前页题目数为空时停止）
                if not questions or len(questions) == 0:
                    logger.info(f"No more questions at page {page}, stopping")
                    break

                logger.info(f"Page {page}: {len(questions)} questions (total: {len(result.questions)})")

            except Exception as e:
                logger.warning(f"Page {page} failed: {e}")
                continue

        result.success = len(result.questions) > 0
        logger.info(f"Paginated crawl completed: {len(result.questions)} questions across {result.total_pages} pages")
        return result


class AWSFAQCrawler:
    """AWS 官方 FAQ 爬虫 - 从 AWS FAQ 页面提取 Q&A 数据

    数据来源: https://aws.amazon.com/{service}/faqs/
    所有数据来自 AWS 官方公开页面，完全合法合规。
    """

    def __init__(self, client: Optional[CrawlerClient] = None):
        self.client = client or CrawlerClient(base_delay=1.0, jitter=0.5)

    def crawl_faq(self, url: str, source: str = "aws_faq") -> CrawlResult:
        """从 AWS FAQ 页面提取问答对作为题目"""
        import json
        from bs4 import BeautifulSoup

        result = CrawlResult(source=source, url=url)
        try:
            resp = self.client.get(url)
            soup = BeautifulSoup(resp.text, "html.parser")
            for script in soup.find_all("script", type="application/ld+json"):
                if not script.string:
                    continue
                try:
                    data = json.loads(script.string)
                except json.JSONDecodeError:
                    continue
                if isinstance(data, dict) and data.get("@type") == "FAQPage":
                    main_entity = data.get("mainEntity", [])
                    if isinstance(main_entity, list):
                        for entity in main_entity:
                            if isinstance(entity, list):
                                for item in entity:
                                    self._add_qa(item, result, url, source)
                            else:
                                self._add_qa(entity, result, url, source)
                    break

            # Strategy 2: Extract from text patterns (fallback)
            if not result.questions:
                body = soup.get_text(separator="\n", strip=True)
                lines = [l.strip() for l in body.split("\n") if l.strip()]
                for i, line in enumerate(lines):
                    if line.startswith("Q:") and len(line) > 15 and len(line) < 500:
                        answer = ""
                        for j in range(i + 1, min(i + 8, len(lines))):
                            if lines[j].startswith("Q:") or lines[j].startswith("Q."):
                                break
                            answer += lines[j] + " "
                        answer = answer.strip()
                        if len(answer) > 30:
                            question_text = line[2:].strip()
                            result.questions.append(ParsedQuestion(
                                content=question_text,
                                question_type="single_choice",
                                difficulty="medium",
                                options=[
                                    {"key": "A", "content": "True", "is_correct": True},
                                    {"key": "B", "content": "False", "is_correct": False},
                                ],
                                explanation=answer,
                                reference_url=url,
                                source=source,
                            ))

            result.success = len(result.questions) > 0
            logger.info(f"AWS FAQ crawl: {len(result.questions)} Q&A from {url}")
        except Exception as e:
            result.error = str(e)
            logger.error(f"AWS FAQ crawl failed {url}: {e}")

        return result

    def _add_qa(self, item: dict, result: CrawlResult, url: str, source: str):
        """Add a single Q&A item as a True/False question if valid"""
        if not isinstance(item, dict) or item.get("@type") != "Question":
            return
        question_text = item.get("name", "").strip()
        answer_data = item.get("acceptedAnswer", {})
        if isinstance(answer_data, dict):
            answer_text = answer_data.get("text", "").strip()
        else:
            answer_text = str(answer_data).strip()

        if not question_text or not answer_text or len(question_text) < 10:
            return

        # Clean HTML from answer text
        answer_text = BeautifulSoup(answer_text, "html.parser").get_text(separator=" ", strip=True)

        result.questions.append(ParsedQuestion(
            content=question_text,
            question_type="single_choice",
            difficulty="medium",
            options=[
                {"key": "A", "content": "True", "is_correct": True},
                {"key": "B", "content": "False", "is_correct": False},
            ],
            explanation=answer_text[:1000],
            reference_url=url,
            source=source,
        ))


# ---------------------------------------------------------------------------
# 预定义来源配置
# ---------------------------------------------------------------------------

# 用户可自行添加更多来源
PREDEFINED_SOURCES = {
    # AWS 官方 FAQ - 完全公开合法，可自由访问
    "aws_ec2_faq": {
        "label": "AWS EC2 官方 FAQ",
        "type": "faq",
        "urls": [
            "https://aws.amazon.com/ec2/faqs/",
        ],
        "description": "Amazon EC2 官方常见问题，涵盖计算服务核心概念",
    },
    "aws_s3_faq": {
        "label": "AWS S3 官方 FAQ",
        "type": "faq",
        "urls": [
            "https://aws.amazon.com/s3/faqs/",
        ],
        "description": "Amazon S3 官方常见问题，涵盖存储服务核心概念",
    },
    "aws_vpc_faq": {
        "label": "AWS VPC 官方 FAQ",
        "type": "faq",
        "urls": [
            "https://aws.amazon.com/vpc/faqs/",
        ],
        "description": "Amazon VPC 官方常见问题，涵盖网络服务核心概念",
    },
    "aws_rds_faq": {
        "label": "AWS RDS 官方 FAQ",
        "type": "faq",
        "urls": [
            "https://aws.amazon.com/rds/faqs/",
        ],
        "description": "Amazon RDS 官方常见问题，涵盖数据库服务核心概念",
    },
    "aws_lambda_faq": {
        "label": "AWS Lambda 官方 FAQ",
        "type": "faq",
        "urls": [
            "https://aws.amazon.com/lambda/faqs/",
        ],
        "description": "AWS Lambda 官方常见问题，涵盖无服务器计算核心概念",
    },
}
