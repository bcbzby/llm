"""
Knowledge article crawler - crawls AWS official documentation pages
and extracts structured knowledge content.
"""
import re
import logging
from typing import Optional
from bs4 import BeautifulSoup
from datetime import datetime

from app.crawler import CrawlerClient
from app.crawler.knowledge_importer import KnowledgeArticleData

logger = logging.getLogger(__name__)


def _clean_text(text: str) -> str:
    """清理HTML文本"""
    import html
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\n+', '\n', text)
    return text


def _detect_category(url: str, title: str, content: str) -> str:
    """从URL和内容中检测文章分类"""
    url_lower = url.lower()
    title_lower = title.lower()
    content_lower = content[:500].lower()

    categories = {
        'compute': ['ec2', 'lambda', 'autoscaling', 'auto scaling', 'compute', 'batch', 'elastic beanstalk',
                     'ecs', 'eks', 'fargate', 'serverless'],
        'storage': ['s3', 'ebs', 'efs', 'storage', 'backup', 'storage gateway'],
        'network': ['vpc', 'cloudfront', 'route53', 'route 53', 'direct connect', 'vpn',
                     'network', 'elb', 'alb', 'nlb', 'api gateway'],
        'database': ['rds', 'dynamodb', 'aurora', 'redshift', 'elasticache', 'database',
                      'documentdb', 'neptune', 'timestream'],
        'security': ['iam', 'kms', 'cloudtrail', 'shield', 'waf', 'guardduty', 'inspector',
                      'security', 'cognito', 'secretes manager'],
        'ai': ['sagemaker', 'rekognition', 'comprehend', 'polly', 'translate', 'textract',
               'kendra', 'bedrock', 'ai', 'machine learning'],
    }

    scores = {}
    for cat, keywords in categories.items():
        score = 0
        for kw in keywords:
            if kw in url_lower:
                score += 3
            if kw in title_lower:
                score += 2
            if kw in content_lower:
                score += 1
        if score > 0:
            scores[cat] = score

    if scores:
        return max(scores, key=scores.get)
    return 'general'


def _extract_aws_doc_content(soup: BeautifulSoup, url: str) -> tuple[str, str, str, str]:
    """从 AWS 官方文档页面提取标题、摘要、正文、分类"""
    title = ""
    summary = ""
    content_parts = []

    # 提取标题
    h1 = soup.select_one('h1, h1.title, .title, #title')
    if h1:
        title = _clean_text(h1.get_text())

    # 提取摘要/描述
    desc = soup.select_one('p.abstract, .description, .subtitle, .shortdesc, meta[name="description"]')
    if desc:
        if desc.name == 'meta':
            summary = desc.get('content', '')
        else:
            summary = _clean_text(desc.get_text())

    # 提取正文 - 优先选择主要内容区
    main_selectors = [
        'main', 'article', '[role="main"]', '#main-content',
        '.main-content', '.content', '.document', '#aws-page-content',
        '.aws-content', '.article-body',
    ]
    main_el = None
    for sel in main_selectors:
        main_el = soup.select_one(sel)
        if main_el:
            break

    if not main_el:
        main_el = soup

    # 提取所有段落和标题
    for tag in main_el.find_all(['h2', 'h3', 'h4', 'p', 'li', 'pre', 'table']):
        text = _clean_text(tag.get_text())
        if not text or len(text) < 10:
            continue

        if tag.name in ('h2', 'h3', 'h4'):
            content_parts.append(f"\n## {text}\n")
        elif tag.name == 'li':
            content_parts.append(f"- {text}")
        elif tag.name == 'pre':
            content_parts.append(f"```\n{text}\n```")
        else:
            content_parts.append(text)

    content = '\n'.join(content_parts)

    # 限制内容长度
    if len(content) > 15000:
        content = content[:15000] + "\n\n...（内容过长已截断）"

    if not title:
        title = "AWS " + url.split('/')[-2].replace('-', ' ').title() if '/' in url else "AWS Service Guide"

    category = _detect_category(url, title, content)

    return title, summary, content, category


# 预定义爬取来源 - AWS 官方文档页面
KNOWLEDGE_SOURCES = {
    "aws_ec2_guide": {
        "label": "Amazon EC2 用户指南",
        "category": "compute",
        "tags": ["EC2", "Compute"],
        "urls": [
            "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html",
            "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-types.html",
            "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-lifecycle.html",
        ],
    },
    "aws_s3_guide": {
        "label": "Amazon S3 用户指南",
        "category": "storage",
        "tags": ["S3", "Storage"],
        "urls": [
            "https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html",
            "https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-classes-intro.html",
        ],
    },
    "aws_vpc_guide": {
        "label": "Amazon VPC 用户指南",
        "category": "network",
        "tags": ["VPC", "Network"],
        "urls": [
            "https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html",
            "https://docs.aws.amazon.com/vpc/latest/userguide/vpc-subnets-ug.html",
            "https://docs.aws.amazon.com/vpc/latest/userguide/vpc-peering.html",
        ],
    },
    "aws_rds_guide": {
        "label": "Amazon RDS 用户指南",
        "category": "database",
        "tags": ["RDS", "Database"],
        "urls": [
            "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html",
            "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.html",
        ],
    },
    "aws_lambda_guide": {
        "label": "AWS Lambda 开发者指南",
        "category": "compute",
        "tags": ["Lambda", "Serverless", "Compute"],
        "urls": [
            "https://docs.aws.amazon.com/lambda/latest/dg/welcome.html",
            "https://docs.aws.amazon.com/lambda/latest/dg/lambda-invocation.html",
        ],
    },
    "aws_dynamodb_guide": {
        "label": "Amazon DynamoDB 开发者指南",
        "category": "database",
        "tags": ["DynamoDB", "Database"],
        "urls": [
            "https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html",
        ],
    },
    "aws_iam_guide": {
        "label": "AWS IAM 用户指南",
        "category": "security",
        "tags": ["IAM", "Security"],
        "urls": [
            "https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html",
            "https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html",
        ],
    },
    "aws_cloudfront_guide": {
        "label": "Amazon CloudFront 开发者指南",
        "category": "network",
        "tags": ["CloudFront", "CDN", "Network"],
        "urls": [
            "https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html",
        ],
    },
    "aws_sagemaker_guide": {
        "label": "Amazon SageMaker 开发者指南",
        "category": "ai",
        "tags": ["SageMaker", "AI/ML"],
        "urls": [
            "https://docs.aws.amazon.com/sagemaker/latest/dg/whatis.html",
        ],
    },
    "aws_elb_guide": {
        "label": "Elastic Load Balancing 用户指南",
        "category": "network",
        "tags": ["ELB", "Network"],
        "urls": [
            "https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/what-is-load-balancing.html",
        ],
    },
    "aws_ecs_guide": {
        "label": "Amazon ECS 开发者指南",
        "category": "compute",
        "tags": ["ECS", "Containers", "Compute"],
        "urls": [
            "https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html",
        ],
    },
}


class KnowledgeCrawler:
    """爬取 AWS 官方文档生成知识文章"""

    def __init__(self, client: Optional[CrawlerClient] = None):
        self.client = client or CrawlerClient(base_delay=3.0, jitter=2.0)

    def crawl_source(self, source_key: str) -> list[KnowledgeArticleData]:
        """爬取单个预定义来源"""
        if source_key not in KNOWLEDGE_SOURCES:
            raise ValueError(f"未知来源: {source_key}")

        config = KNOWLEDGE_SOURCES[source_key]
        articles = []
        provider = "aws"
        category = config["category"]
        tags = config["tags"]

        for url in config["urls"]:
            try:
                title, summary, content, detected_cat = self._crawl_page(url)
                if not content or len(content) < 100:
                    logger.warning(f"Skipping {url}: content too short ({len(content or '')})")
                    continue

                # 使用预定义分类，如果没有检测到则使用预定义
                final_category = detected_cat if detected_cat != 'general' else category

                article = KnowledgeArticleData(
                    title=title,
                    content=content,
                    provider=provider,
                    category=final_category,
                    summary=summary or content[:150],
                    tags=tags,
                    source_url=url,
                )
                articles.append(article)
                logger.info(f"Crawled: {title} ({len(content)} chars)")

            except Exception as e:
                logger.error(f"Failed to crawl {url}: {e}")

        return articles

    def crawl_all(self) -> list[KnowledgeArticleData]:
        """爬取所有预定义来源"""
        all_articles = []
        for key in KNOWLEDGE_SOURCES:
            try:
                articles = self.crawl_source(key)
                all_articles.extend(articles)
                logger.info(f"Source {key}: {len(articles)} articles")
            except Exception as e:
                logger.error(f"Source {key} failed: {e}")
        return all_articles

    def crawl_url(self, url: str, category: str = "general", tags: list[str] = None) -> Optional[KnowledgeArticleData]:
        """爬取单个URL"""
        try:
            title, summary, content, detected_cat = self._crawl_page(url)
            if not content or len(content) < 100:
                return None

            final_cat = detected_cat if detected_cat != 'general' else category

            return KnowledgeArticleData(
                title=title,
                content=content,
                provider="aws",
                category=final_cat,
                summary=summary or content[:150],
                tags=tags or [final_cat],
                source_url=url,
            )
        except Exception as e:
            logger.error(f"Failed to crawl {url}: {e}")
            return None

    def _crawl_page(self, url: str) -> tuple[str, str, str, str]:
        """爬取单个页面，返回 (title, summary, content, category)"""
        resp = self.client.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        return _extract_aws_doc_content(soup, url)
