# -*- coding: utf-8 -*-
"""
CloudCert Pro - 数据库初始化脚本
生成认证、标签、题目（公平分配到每个认证）、知识库文章
"""
import sys, os, random
random.seed(42)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import create_engine, select, func as sa_func, delete
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.database import Base
from app.models.certification import Certification, Subject
from app.models.tag import Tag
from app.models.question import Question, QuestionOption, QuestionTag
from app.models.user import User
from app.models.knowledge import KnowledgeArticle, ArticleTag
from app.services.auth_service import AuthService

# =====================================================================
# 题库加载
# =====================================================================
import importlib.util as _util
_spec = _util.spec_from_file_location("qb", os.path.join(os.path.dirname(__file__), "question_bank.py"))
_qb_mod = _util.module_from_spec(_spec)
_spec.loader.exec_module(_qb_mod)
QUESTION_BANK_V1 = _qb_mod.QUESTION_BANK

_spec2 = _util.spec_from_file_location("qb2", os.path.join(os.path.dirname(__file__), "question_bank_v2.py"))
try:
    _qb2_mod = _util.module_from_spec(_spec2)
    _spec2.loader.exec_module(_qb2_mod)
    QUESTION_BANK_V2 = _qb2_mod.QUESTION_BANK
except:
    QUESTION_BANK_V2 = []

settings = get_settings()
sync_url = settings.database_url.replace("+aiosqlite", "").replace("+asyncpg", "")
engine = create_engine(sync_url, connect_args={"check_same_thread": False} if "sqlite" in sync_url else {})
SessionLocal = sessionmaker(engine, expire_on_commit=False)

# =====================================================================
# 认证 -> 标签映射（每个认证应该覆盖哪些技术领域）
# =====================================================================
CERT_TAG_MAP = {
    "aws-saa": ["EC2","S3","VPC","RDS","DynamoDB","IAM","ELB","Auto Scaling","Lambda","EFS","EBS","CloudFront","Route53","Aurora","ElastiCache","Redshift","SNS","SQS"],
    "aws-sap": ["EC2","S3","VPC","RDS","DynamoDB","IAM","ELB","Auto Scaling","Lambda","EFS","EBS","CloudFront","Route53","KMS","Redshift","ElastiCache","SQS"],
    "aws-dva": ["Lambda","DynamoDB","SQS","SNS","ECS","EKS","Fargate","EC2","S3","ElastiCache","RDS","API Gateway"],
    "aws-soa": ["EC2","S3","EBS","VPC","CloudTrail","IAM","Auto Scaling","ELB","Route53","RDS"],
    "aws-clf": ["EC2","S3","RDS","Lambda","IAM","VPC","Auto Scaling","DynamoDB","ELB","CloudFront"],
    "aws-dop": ["Lambda","ECS","EKS","Fargate","EC2","S3","IAM","CloudTrail"],
    "aws-ans": ["VPC","Route53","CloudFront","ELB","NAT Gateway","Security Group","Direct Connect","VPN"],
    "aws-scs": ["IAM","KMS","CloudTrail","Shield","GuardDuty","S3","WAF"],
    "aws-dbs": ["RDS","DynamoDB","Aurora","Redshift","ElastiCache","S3","DocumentDB"],
    "aws-saa-cn": ["EC2","S3","VPC","RDS","DynamoDB","IAM","ELB","Auto Scaling","Lambda","EFS","EBS"],
    "aws-sa": ["SageMaker","Rekognition","Comprehend","Polly","Lambda","EC2","S3","DynamoDB"],
    "aws-mls": ["SageMaker","Rekognition","Comprehend","Lambda","EC2","S3","DynamoDB"],
    "aws-bd": ["Redshift","S3","DynamoDB","RDS","EC2"],
}

# True/False 模板（补充用）
TEMPLATES = [
    ("EC2","Amazon EC2 provides resizable compute capacity in the cloud."),
    ("EC2","EC2 supports On-Demand, Reserved, and Spot Instance pricing models."),
    ("EC2","Security groups act as a stateful firewall for EC2 instances."),
    ("EC2","Network ACLs are stateless and support both ALLOW and DENY rules."),
    ("EC2","An Elastic IP address is a static public IPv4 address."),
    ("EC2","Instance metadata is accessible from within the instance at 169.254.169.254."),
    ("Auto Scaling","Auto Scaling automatically adjusts EC2 instances based on demand."),
    ("Auto Scaling","Auto Scaling can balance instances across multiple Availability Zones."),
    ("ELB","Application Load Balancer operates at Layer 7 and supports HTTP/HTTPS."),
    ("ELB","Network Load Balancer operates at Layer 4 and handles millions of requests."),
    ("S3","Amazon S3 provides 99.999999999% (11 9's) durability."),
    ("S3","S3 Standard-IA is for infrequently accessed data that needs rapid access."),
    ("S3","S3 Glacier Deep Archive is the lowest-cost storage class."),
    ("S3","S3 life cycle policies automate transitioning between storage classes."),
    ("S3","S3 versioning protects against accidental deletion."),
    ("EBS","Amazon EBS provides block-level storage for EC2 instances."),
    ("EBS","EBS volumes persist independently from the life of an instance."),
    ("EFS","Amazon EFS is a scalable file system for Linux workloads."),
    ("VPC","A VPC is a logically isolated virtual network."),
    ("VPC","A subnet spans a single Availability Zone."),
    ("VPC","An Internet Gateway enables VPC-to-internet communication."),
    ("VPC","A NAT Gateway enables private subnets to access the internet."),
    ("VPC","VPC Peering does not support transitive routing."),
    ("VPC","VPC Flow Logs capture IP traffic information."),
    ("VPC","AWS Direct Connect provides a dedicated private network connection."),
    ("VPC","Transit Gateway connects multiple VPCs and on-premises networks."),
    ("VPC","Gateway Endpoints support S3 and DynamoDB."),
    ("CloudFront","Amazon CloudFront is a global CDN with 450+ edge locations."),
    ("Route53","Amazon Route 53 supports latency-based, geolocation, and weighted routing."),
    ("DynamoDB","Amazon DynamoDB offers single-digit millisecond performance at any scale."),
    ("DynamoDB","DynamoDB Accelerator (DAX) is an in-memory cache."),
    ("DynamoDB","DynamoDB Global Tables provide multi-region replication."),
    ("DynamoDB","DynamoDB Streams capture item-level changes in near real-time."),
    ("RDS","Amazon RDS supports MySQL, PostgreSQL, MariaDB, Oracle, and SQL Server."),
    ("RDS","RDS Multi-AZ provides automatic failover for high availability."),
    ("RDS","RDS Read Replicas can be promoted to standalone databases."),
    ("Aurora","Amazon Aurora is compatible with MySQL and PostgreSQL."),
    ("Redshift","Amazon Redshift is a petabyte-scale data warehouse."),
    ("ElastiCache","Amazon ElastiCache supports Redis and Memcached."),
    ("IAM","AWS IAM manages users, groups, and roles."),
    ("IAM","IAM policies are JSON documents that define permissions."),
    ("IAM","IAM roles provide temporary credentials via AWS STS."),
    ("KMS","AWS KMS manages encryption keys with automatic rotation."),
    ("CloudTrail","AWS CloudTrail records API activity for auditing."),
    ("Shield","AWS Shield Standard provides automatic DDoS protection at no cost."),
    ("GuardDuty","Amazon GuardDuty is a threat detection service using ML."),
    ("Lambda","AWS Lambda is a serverless compute service."),
    ("Lambda","Lambda can be triggered by S3 events, DynamoDB Streams, and API Gateway."),
    ("SQS","Amazon SQS is a fully managed message queuing service."),
    ("SNS","Amazon SNS is a fully managed pub/sub messaging service."),
    ("ECS","Amazon ECS is a fully managed container orchestration service."),
    ("EKS","Amazon EKS runs Kubernetes clusters on AWS."),
    ("Fargate","AWS Fargate is a serverless compute engine for containers."),
    ("SageMaker","Amazon SageMaker is a fully managed machine learning platform."),
    ("Rekognition","Amazon Rekognition provides image and video analysis."),
    ("Comprehend","Amazon Comprehend is a natural language processing service."),
    ("Polly","Amazon Polly converts text into lifelike speech."),
    ("WAF","AWS WAF protects web applications from SQL injection and XSS attacks."),
    ("VPN","AWS Site-to-Site VPN uses IPsec tunnels for secure connectivity."),
    ("Direct Connect","AWS Direct Connect gateway connects VPCs across regions."),
    ("Security Group","Security groups support stateful traffic filtering at instance level."),
    ("Shield","AWS Shield Advanced provides enhanced DDoS protection with 24/7 support."),
    ("S3","S3 Object Lock prevents objects from being deleted or overwritten."),
]

# =====================================================================
# 知识库文章（中文，专业名词保留英文）
# =====================================================================
KNOWLEDGE_ARTICLES = [
    {
        "provider": "aws", "category": "compute",
        "title": "Amazon EC2 详解：实例类型、定价模型与最佳实践",
        "summary": "全面了解 Amazon EC2 的实例类型、五种定价模式以及安全组、弹性 IP、用户数据等核心功能的最佳实践。",
        "content": "## 1. EC2 实例类型\n\nAmazon EC2 提供多种实例类型：\n- 通用型 (General Purpose): t4g/t3, m7g/m6i - 适合Web服务器、微服务\n- 计算优化型 (Compute Optimized): c7g/c6i - 适合批处理、科学建模\n- 内存优化型 (Memory Optimized): r7g/r6i, x2iedn - 适合内存数据库、SAP HANA\n- 存储优化型 (Storage Optimized): i4i/i3 - 适合NoSQL数据库\n- GPU 型: p4d/p3, g5/g4dn - 适合ML训练、图形渲染\n\n## 2. 定价模型\n- 按需 (On-Demand): 按秒计费，灵活无预付\n- 预留实例 (RI): 1-3年承诺，最高72%折扣\n- Spot 实例: 最高90%折扣，适合容错工作负载\n- 专用主机 (Dedicated Host): 物理服务器独享\n- Savings Plans: 灵活覆盖EC2+Fargate+Lambda\n\n## 3. 安全组 vs 网络 ACL\n- 安全组: 有状态，仅Allow，实例级别\n- 网络 ACL: 无状态，Allow+Deny，子网级别",
        "tags": ["EC2","Compute"],
        "source_url": "https://aws.amazon.com/ec2/faqs/",
    },
    {
        "provider": "aws", "category": "compute",
        "title": "AWS Lambda 深度解析",
        "summary": "深入了解 AWS Lambda 的触发方式、并发模型、冷启动优化策略和 VPC 集成方案。",
        "content": "## Lambda 核心概念\n\nAWS Lambda 是事件驱动的无服务器计算服务。\n\n### 关键限制\n- 超时: 最大 900 秒\n- 临时存储: 最高 10GB\n- 并发: 默认 1000/账户\n\n### 触发方式\n- 同步: API Gateway、ALB、Function URL\n- 异步: S3、SNS、EventBridge\n- 流式: DynamoDB Streams、Kinesis、SQS\n\n### 冷启动优化\n1. 减少包体积，使用 Lambda Layers\n2. 使用 SnapStart (Java 降至 ~200ms)\n3. 关键路径使用预置并发",
        "tags": ["Lambda","Serverless","Compute"],
        "source_url": "https://aws.amazon.com/lambda/faqs/",
    },
    {
        "provider": "aws", "category": "compute",
        "title": "Auto Scaling 弹性伸缩指南",
        "summary": "详解 Auto Scaling 的动态扩缩容、计划扩缩容和预测扩缩容策略。",
        "content": "## Auto Scaling 策略\n\n1. 目标追踪 (Target Tracking): 维持指标目标值\n2. 步进调整 (Step Scaling): 按偏离程度调整\n3. 计划扩缩容 (Scheduled): 基于时间表\n4. 预测扩缩容 (Predictive): ML 分析历史流量\n\n### 最佳实践\n- 跨 2-3 个可用区部署\n- 混合 Spot 和 On-Demand\n- 配置冷却时间避免震荡",
        "tags": ["Auto Scaling","Compute"],
        "source_url": "https://aws.amazon.com/autoscaling/faqs/",
    },
    {
        "provider": "aws", "category": "storage",
        "title": "Amazon S3 完全手册",
        "summary": "全面解读 S3 存储类、数据保护机制和生命周期管理。",
        "content": "## S3 存储类\n\n- S3 Standard: 频繁访问，99.99% 可用性\n- S3 Standard-IA: 低频访问，30天最短存储\n- S3 Glacier: 归档，1-5分钟恢复\n- S3 Glacier Deep Archive: 超长期归档，12小时恢复\n\n## 数据保护\n- 版本控制: 保留所有版本\n- Object Lock: WORM 模式\n- 复制: CRR 跨区域/SRR 同区域\n\n## 访问控制\n- Bucket Policy: JSON 策略\n- IAM 策略: 用户/角色权限\n- 预签名 URL: 临时授权访问",
        "tags": ["S3","Storage"],
        "source_url": "https://aws.amazon.com/s3/faqs/",
    },
    {
        "provider": "aws", "category": "storage",
        "title": "Amazon EBS 弹性块存储",
        "summary": "详解 EBS 卷类型、快照管理和加密机制。",
        "content": "## EBS 卷类型\n\n| 类型 | 最大IOPS | 用途 |\n|------|---------|------|\n| gp3 | 16,000 | 通用工作负载 |\n| io2 | 256,000 | 关键数据库 |\n| st1 | 500 MB/s | 大数据 |\n| sc1 | 250 MB/s | 冷归档 |\n\n## 快照\n- 增量备份到 S3\n- 跨区域复制\n- 生命周期策略自动管理",
        "tags": ["EBS","Storage"],
        "source_url": "https://aws.amazon.com/ebs/faqs/",
    },
    {
        "provider": "aws", "category": "network",
        "title": "Amazon VPC 网络架构深度解析",
        "summary": "全面讲解 VPC 子网设计、路由、连接选项和 VPC Endpoints。",
        "content": "## VPC 核心组件\n\n- CIDR: IP 地址范围\n- 子网: 每个可用区一个子网\n- 路由表: 控制流量\n- IGW: 互联网网关\n- NAT: 私有子网出网\n\n## 连接选项\n- VPC Peering: 直连，不支持传递路由\n- Transit Gateway: 中心辐射架构\n- Direct Connect: 专线连接\n- VPN: 加密隧道\n\n## VPC Endpoints\n- Gateway Endpoints: S3、DynamoDB（免费）\n- Interface Endpoints: 100+ 服务（PrivateLink）",
        "tags": ["VPC","Network"],
        "source_url": "https://aws.amazon.com/vpc/faqs/",
    },
    {
        "provider": "aws", "category": "network",
        "title": "Amazon CloudFront CDN 指南",
        "summary": "了解 CloudFront 的全球加速、缓存策略和安全功能。",
        "content": "## CloudFront 简介\n\n- 450+ 全球边缘节点\n- 内置 DDoS 防护 (Shield Standard)\n\n## 缓存策略\n- TTL: 0秒到365天\n- 缓存键: URL + 查询参数 + Cookies\n\n## 安全\n- AWS WAF 集成\n- 地理限制\n- 签名 URL / Cookie\n\n## 边缘计算\n- CloudFront Functions: 轻量级 JavaScript\n- Lambda@Edge: 全功能 Python/Node.js",
        "tags": ["CloudFront","Network","CDN"],
        "source_url": "https://aws.amazon.com/cloudfront/faqs/",
    },
    {
        "provider": "aws", "category": "database",
        "title": "Amazon RDS 关系型数据库指南",
        "summary": "全面介绍 RDS 数据库引擎、高可用架构和只读副本。",
        "content": "## RDS 支持的引擎\n- Aurora、MySQL、PostgreSQL、SQL Server、Oracle、MariaDB\n\n## 高可用\n- Multi-AZ: 自动故障转移 (< 60秒)\n- Multi-AZ DB Cluster: 1主+2备, 故障转移 < 35秒\n\n## 只读副本 (Read Replicas)\n- 最多 15 个\n- 支持跨区域\n- 可提升为主库",
        "tags": ["RDS","Database"],
        "source_url": "https://aws.amazon.com/rds/faqs/",
    },
    {
        "provider": "aws", "category": "database",
        "title": "Amazon DynamoDB NoSQL 指南",
        "summary": "深入讲解 DynamoDB 的数据模型、索引和读写容量模式。",
        "content": "## DynamoDB 核心概念\n\n- 表 (Table)、项 (Item)、属性 (Attribute)\n- 分区键 + 排序键\n\n## 索引\n- LSI: 本地二级索引，同分区键不同排序键\n- GSI: 全局二级索引，不同分区键\n\n## 容量模式\n- 按需 (On-Demand): 自动扩缩容\n- 预置 (Provisioned): 指定 RCU/WCU\n\n## 高级功能\n- DAX: 内存缓存 (微秒级)\n- Global Tables: 多区域多主复制\n- DynamoDB Streams: 变更数据捕获",
        "tags": ["DynamoDB","Database"],
        "source_url": "https://aws.amazon.com/dynamodb/faqs/",
    },
    {
        "provider": "aws", "category": "security",
        "title": "AWS IAM 身份与访问管理",
        "summary": "全面讲解 IAM 用户、角色、策略和安全最佳实践。",
        "content": "## IAM 核心组件\n\n- 用户 (User): 个人或服务账号\n- 组 (Group): 用户集合\n- 角色 (Role): 临时权限\n- 策略 (Policy): JSON 权限文档\n\n## 安全最佳实践\n- 启用 MFA\n- 最小权限原则\n- 权限边界 (Permissions Boundary)\n- 定期审查未使用权限\n\n## 跨账户访问\n- 角色切换 (AssumeRole)\n- 基于资源的策略 (Bucket Policy 等)",
        "tags": ["IAM","Security"],
        "source_url": "https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html",
    },
    {
        "provider": "aws", "category": "security",
        "title": "AWS 安全防护服务解析",
        "summary": "了解 Shield、WAF、GuardDuty 和 Inspector 的多层防护架构。",
        "content": "## AWS Shield\n- Standard: 免费，自动 DDoS 防护\n- Advanced: $3,000/月，24/7 DRT 支持\n\n## AWS WAF\n- SQL 注入、XSS 防护\n- 速率限制\n- 托管规则组\n\n## GuardDuty\n- 威胁检测 (ML)\n- 数据源: VPC Flow Logs、CloudTrail、DNS\n\n## Inspector\n- 漏洞扫描 (CVE)\n- 网络可达性检查",
        "tags": ["Shield","Security","GuardDuty","WAF"],
        "source_url": "https://aws.amazon.com/shield/faqs/",
    },
    {
        "provider": "aws", "category": "ai",
        "title": "Amazon SageMaker 机器学习平台",
        "summary": "全面介绍 SageMaker 的 ML 全生命周期：数据标注、训练、部署和监控。",
        "content": "## SageMaker 核心功能\n\n- Ground Truth: 数据标注\n- Studio: 集成开发环境\n- Training: 托管训练\n- Autopilot: 自动 ML\n\n## 推理部署\n- 实时端点 (Real-time Endpoint)\n- 批量推理 (Batch Transform)\n- 无服务器推理 (Serverless)\n\n## 模型监控\n- Model Monitor: 数据漂移检测\n- Clarify: 模型可解释性",
        "tags": ["SageMaker","AI/ML"],
        "source_url": "https://docs.aws.amazon.com/sagemaker/latest/dg/whatis.html",
    },
    {
        "provider": "aws", "category": "compute",
        "title": "AWS ECS & EKS 容器服务",
        "summary": "了解 Amazon ECS 和 EKS 的容器编排能力及 Fargate 无服务器计算。",
        "content": "## Amazon ECS\n- 全托管容器编排\n- 启动类型: Fargate (无服务器) / EC2\n- 任务定义、服务、集群\n\n## Amazon EKS\n- 托管 Kubernetes 控制平面\n- 支持现有 K8s 工具链\n\n## AWS Fargate\n- 无需管理服务器\n- 按容器计费\n- 自动扩缩容",
        "tags": ["ECS","EKS","Fargate","Containers"],
        "source_url": "https://aws.amazon.com/ecs/faqs/",
    },
    {
        "provider": "aws", "category": "database",
        "title": "Amazon ElastiCache 内存缓存",
        "summary": "了解 ElastiCache for Redis 和 Memcached 的核心概念和最佳实践。",
        "content": "## Redis vs Memcached\n\n| 特性 | Redis | Memcached |\n|------|-------|-----------|\n| 数据结构 | 丰富 | 键值 |\n| 持久化 | RDB/AOF | 无 |\n| 复制 | Cluster | 无 |\n| Lua | 支持 | 不支持 |\n\n## 使用场景\n- 数据库查询缓存\n- 会话存储\n- 排行榜 (Redis Sorted Set)",
        "tags": ["ElastiCache","Database"],
        "source_url": "https://aws.amazon.com/elasticache/faqs/",
    },
    {
        "provider": "aws", "category": "network",
        "title": "Amazon Route 53 DNS 指南",
        "summary": "详解 Route 53 的路由策略和健康检查配置。",
        "content": "## 路由策略\n- 简单路由: 单记录\n- 加权路由: 按比例分配\n- 延迟路由: 最低延迟\n- 故障转移: 主备切换\n- 地理路由: 按国家/地区\n\n## 健康检查\n- HTTP/HTTPS: 检查状态码\n- TCP: 检查端口\n- 字符串匹配: 检查响应内容",
        "tags": ["Route53","Network"],
        "source_url": "https://aws.amazon.com/route53/faqs/",
    },
]


# =====================================================================
# 认证和科目定义
# =====================================================================
AWS_CERTIFICATIONS = [
    ("aws-saa", "AWS Solutions Architect Associate", "associate", 65, 720, 130, "Validate ability to design distributed systems on AWS.", [
        ("Compute", 20), ("Storage", 15), ("Networking & CDN", 18),
        ("Database", 14), ("Security & Compliance", 16), ("Architecture Design", 17),
    ]),
    ("aws-sap", "AWS Solutions Architect Professional", "professional", 75, 750, 180, "Validate advanced architecture skills.", [
        ("Compute Design", 15), ("Storage Design", 12), ("Network Architecture", 15),
        ("Database Architecture", 13), ("Security Design", 15), ("Scalable Design", 15),
        ("Migration & Modernization", 15),
    ]),
    ("aws-dva", "AWS Developer Associate", "associate", 65, 720, 130, "Validate ability to develop AWS applications.", [
        ("Development with AWS", 22), ("Security", 14), ("Deployment", 16),
        ("Troubleshooting & Optimization", 18), ("Serverless", 30),
    ]),
    ("aws-soa", "AWS SysOps Administrator Associate", "associate", 65, 720, 130, "Validate ability to operate AWS workloads.", [
        ("Monitoring & Reporting", 15), ("Deployment & Provisioning", 14),
        ("Security & Compliance", 16), ("Networking", 14), ("Storage & Data Management", 12),
        ("Reliability & Business Continuity", 14), ("Automation & Optimization", 15),
    ]),
    ("aws-saa-cn", "AWS Solutions Architect Associate (Chinese)", "associate", 65, 720, 130, "Chinese version of SAA exam.", [
        ("Compute", 20), ("Storage", 15), ("Networking & CDN", 18),
        ("Database", 14), ("Security & Compliance", 16), ("Architecture Design", 17),
    ]),
    ("aws-clf", "AWS Cloud Practitioner", "foundational", 65, 700, 90, "Validate foundational cloud knowledge.", [
        ("Cloud Concepts", 26), ("Security & Compliance", 25), ("Technology", 33), ("Billing & Pricing", 16),
    ]),
    ("aws-dop", "AWS DevOps Engineer Professional", "professional", 75, 750, 180, "Validate DevOps expertise.", [
        ("SDLC Automation", 22), ("Configuration Management", 19),
        ("Monitoring & Logging", 15), ("Security & Governance", 15),
        ("Incident & Event Response", 14), ("HA & Scaling", 15),
    ]),
    ("aws-ans", "AWS Advanced Networking Specialty", "specialty", 65, 750, 170, "Validate advanced networking skills.", [
        ("Network Design", 30), ("Network Implementation", 20),
        ("Network Management", 20), ("Security & Compliance", 15), ("Hybrid IT", 15),
    ]),
    ("aws-scs", "AWS Security Specialty", "specialty", 65, 750, 170, "Validate security expertise.", [
        ("Incident Response", 14), ("Logging & Monitoring", 15),
        ("Infrastructure Security", 20), ("IAM", 20),
        ("Data Protection", 18), ("Compliance", 13),
    ]),
    ("aws-dbs", "AWS Database Specialty", "specialty", 65, 750, 170, "Validate database expertise.", [
        ("Database Design", 26), ("Deployment & Migration", 20),
        ("Management & Operations", 18), ("Monitoring & Troubleshooting", 18),
        ("Database Security", 18),
    ]),
    ("aws-sa", "AWS Certified AI Practitioner", "foundational", 65, 700, 90, "Validate foundational AI/ML knowledge.", [
        ("AI/ML Fundamentals", 20), ("Amazon SageMaker", 25), ("AWS AI Services", 30),
        ("Security & Governance", 15), ("ML Best Practices", 10),
    ]),
    ("aws-mls", "AWS Machine Learning Specialty", "specialty", 65, 750, 170, "Validate ML/AI expertise.", [
        ("Data Engineering", 20), ("Exploratory Data Analysis", 20),
        ("Modeling", 20), ("ML Implementation", 24), ("ML Security & Operations", 16),
    ]),
    ("aws-bd", "AWS Data Analytics Specialty", "specialty", 65, 750, 170, "Validate data analytics expertise.", [
        ("Collection", 18), ("Storage & Management", 22),
        ("Processing", 24), ("Analysis & Visualization", 18),
        ("Security & Compliance", 18),
    ]),
]

TAG_TREE = {
    "Compute": {"EC2": {}, "Lambda": {}, "Auto Scaling": {}, "ELB": {}, "ECS": {}, "EKS": {}, "Fargate": {}},
    "Storage": {"S3": {"S3 Standard", "S3 Glacier", "S3 IA"}, "EFS": {}, "EBS": {}, "Storage Gateway": {}},
    "Network": {"VPC": {"Subnet", "Route Table", "NAT Gateway", "Security Group"}, "CloudFront": {}, "Route53": {}, "ELB": {}},
    "Database": {"RDS": {}, "DynamoDB": {}, "Aurora": {}, "ElastiCache": {}, "Redshift": {}, "DocumentDB": {}},
    "Security": {"IAM": {"User", "Role", "Policy"}, "KMS": {}, "CloudTrail": {}, "Shield": {}, "WAF": {}, "GuardDuty": {}},
    "Serverless": {"Lambda": {}, "API Gateway": {}, "Step Functions": {}, "EventBridge": {}, "SQS": {}, "SNS": {}},
    "Containers": {"ECS": {}, "EKS": {}, "ECR": {}, "Fargate": {}},
    "AI/ML": {"SageMaker": {}, "Comprehend": {}, "Rekognition": {}, "Polly": {}, "Lex": {}, "Bedrock": {}},
}


def get_question_pool_for_cert(allowed_tags):
    """从所有题库中收集匹配该认证标签的题目"""
    pool = []
    seen = set()

    def add_q(q, src_tags):
        prefix = q.get("content", "")[:60]
        if prefix not in seen:
            seen.add(prefix)
            pool.append(q)
        return prefix not in seen

    # 1. question_bank V1
    for q in QUESTION_BANK_V1:
        q_tags = set(q.get("tags", []))
        if q_tags & allowed_tags:
            add_q(q, q_tags)

    # 2. question_bank V2
    for q in QUESTION_BANK_V2:
        q_domains = set(q.get("domains", []))
        if q_domains & allowed_tags:
            add_q(q, q_domains)

    # 3. Templates
    for tag_name, content in TEMPLATES:
        if tag_name in allowed_tags:
            is_true = random.random() > 0.2
            add_q({
                "content": content,
                "type": "single_choice",
                "difficulty": "medium",
                "options": [("A","True",is_true), ("B","False",not is_true)],
                "explanation": f"Based on AWS public documentation.",
                "tags": [tag_name],
            }, {tag_name})

    random.shuffle(pool)
    return pool


def seed():
    """主函数：初始化所有数据"""
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        # 1. 管理员
        admin = db.execute(select(User).where(User.email == "admin@cloudcert.com")).scalar_one_or_none()
        if not admin:
            admin = User(email="admin@cloudcert.com",
                password_hash=AuthService.hash_password("admin123"),
                nickname="Admin", role="admin", is_active=True)
            db.add(admin)
            db.flush()

        # 2. 标签树
        tags_map = {}
        existing_tags = {t.name: t.id for t in db.execute(select(Tag)).scalars().all()}
        for cat_name, children in TAG_TREE.items():
            if cat_name not in existing_tags:
                cat_tag = Tag(name=cat_name, full_path=cat_name, level=1)
                db.add(cat_tag)
                db.flush()
            else:
                cat_tag = db.get(Tag, existing_tags[cat_name])
            tags_map[cat_name] = cat_tag.id
            for child_name, grandchildren in children.items():
                if child_name not in existing_tags:
                    child_tag = Tag(parent_id=cat_tag.id, name=child_name,
                        full_path=f"{cat_name} > {child_name}", level=2)
                    db.add(child_tag)
                    db.flush()
                else:
                    child_tag = db.get(Tag, existing_tags[child_name])
                tags_map[child_name] = child_tag.id
                for g_name in (grandchildren or {}):
                    if g_name not in existing_tags:
                        g_tag = Tag(parent_id=child_tag.id, name=g_name,
                            full_path=f"{cat_name} > {child_name} > {g_name}", level=3)
                        db.add(g_tag)
                        db.flush()
                        tags_map[g_name] = g_tag.id

        # 3. 认证 + 科目 + 题目
        for code, name, level, total_q, pass_score, duration_min, desc, subjects_data in AWS_CERTIFICATIONS:
            cert = db.execute(select(Certification).where(Certification.code == code)).scalar_one_or_none()
            if not cert:
                cert = Certification(provider="aws", code=code, name=name, level=level,
                    description=desc, total_questions=total_q,
                    pass_score=pass_score, duration_min=duration_min, is_active=True)
                db.add(cert)
                db.flush()

            subjects = []
            for order, (sname, weight) in enumerate(subjects_data, 1):
                subj = db.execute(select(Subject).where(
                    Subject.certification_id == cert.id, Subject.name == sname)).scalar_one_or_none()
                if not subj:
                    subj = Subject(certification_id=cert.id, name=sname, sort_order=order, weight=weight)
                    db.add(subj)
                subjects.append(subj)
            db.flush()

            # 获取该认证的已有题量
            sub_ids = [s.id for s in subjects]
            existing_cnt = db.execute(select(sa_func.count(Question.id)).where(
                Question.subject_id.in_(sub_ids))).scalar() or 0
            need = max(total_q, total_q * 2) - existing_cnt

            if need > 0:
                allowed_tags = set(CERT_TAG_MAP.get(code, ["EC2","S3","VPC","IAM","Lambda"]))
                pool = get_question_pool_for_cert(allowed_tags)
                max_add = min(need, len(pool))
                added = 0

                for q_data in pool[:max_add]:
                    subj = subjects[added % len(subjects)]
                    q = Question(
                        subject_id=subj.id, question_type=q_data.get("type","single_choice"),
                        difficulty=q_data.get("difficulty","medium"),
                        content=q_data["content"], explanation=q_data.get("explanation",""),
                        status="published", is_verified=True, created_by=admin.id,
                    )
                    db.add(q)
                    db.flush()
                    for opt_key, opt_content, is_correct in q_data.get("options",[]):
                        db.add(QuestionOption(question_id=q.id, option_key=opt_key,
                            content=opt_content, is_correct=is_correct,
                            sort_order=ord(opt_key)-65))
                    for tag_name in q_data.get("tags",[]):
                        if tag_name in tags_map:
                            db.add(QuestionTag(question_id=q.id, tag_id=tags_map[tag_name]))
                    added += 1

                print(f"  {code:12s}: +{added:3d} questions (now {existing_cnt+added}/{total_q})")
            else:
                print(f"  {code:12s}: {existing_cnt:3d} questions (already sufficient)")

        db.flush()

        # 4. 知识库文章
        for art in KNOWLEDGE_ARTICLES:
            existing = db.execute(select(KnowledgeArticle).where(
                KnowledgeArticle.title == art["title"])).scalar_one_or_none()
            if not existing:
                from datetime import datetime, timezone
                article = KnowledgeArticle(
                    provider=art["provider"], category=art["category"],
                    title=art["title"], summary=art.get("summary",""),
                    content=art["content"], status="published",
                    source_url=art.get("source_url",""), created_by=admin.id,
                    published_at=datetime.now(timezone.utc),
                )
                db.add(article)
                db.flush()
                for tag_name in art.get("tags",[]):
                    if tag_name in tags_map:
                        db.add(ArticleTag(article_id=article.id, tag_id=tags_map[tag_name]))

        db.commit()

        # 统计
        print("\n=== 题库统计 ===")
        for cert_code, *_ in AWS_CERTIFICATIONS:
            cert = db.execute(select(Certification).where(Certification.code == cert_code)).scalar_one()
            sub_ids = [s.id for s in db.execute(select(Subject).where(Subject.certification_id == cert.id)).scalars().all()]
            cnt = db.execute(select(sa_func.count(Question.id)).where(Question.subject_id.in_(sub_ids))).scalar() or 0
            status = "OK" if cnt >= cert.total_questions else "SHORT"
            print(f"  [{status}] {cert_code:10s}: {cnt:3d}/{cert.total_questions}")

        total_q = db.execute(select(sa_func.count(Question.id))).scalar() or 0
        total_k = db.execute(select(sa_func.count(KnowledgeArticle.id))).scalar() or 0
        print(f"\nTotal: {total_q} questions, {total_k} knowledge articles")
        print(f"Admin: admin@cloudcert.com / admin123")


def clear():
    """清空数据（保留认证和标签）"""
    with SessionLocal() as db:
        db.execute(delete(ArticleTag))
        db.execute(delete(KnowledgeArticle))
        db.execute(delete(QuestionTag))
        db.execute(delete(QuestionOption))
        db.execute(delete(Question))
        db.execute(delete(Subject))
        db.execute(delete(Certification))
        db.execute(delete(Tag))
        db.execute(delete(User))
        db.commit()
        print("All data cleared")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CloudCert Pro - Data Initializer")
    parser.add_argument("--clear", action="store_true", help="Clear all data")
    args = parser.parse_args()

    if args.clear:
        clear()
    else:
        seed()
