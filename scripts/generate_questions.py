"""
CloudCert Pro - 定时题目生成器
================================
用法:
  # 手动运行一次（所有来源）
  python scripts/generate_questions.py --all

  # 仅爬取 AWS FAQ
  python scripts/generate_questions.py --crawl-faq

  # 仅生成程序化题目
  python scripts/generate_questions.py --generate

  # 查看当前题库统计
  python scripts/generate_questions.py --stats

部署配置:
  Linux cron (每天凌晨2点):
    0 2 * * * cd /opt/cloudcert-pro && /usr/bin/python3 scripts/generate_questions.py --all >> logs/generate.log 2>&1

  Windows 任务计划:
    powershell -Command "& 'C:\code\.venv\Scripts\python.exe' C:\code\cloudcert-pro\scripts\generate_questions.py --all"
"""
import sys
import os
import argparse
import random
from datetime import datetime

# 确保能找到 backend 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import SessionLocal
from app.models.question import Question, QuestionOption, QuestionTag
from app.models.tag import Tag
from app.models.certification import Subject, Certification
from app.models.user import User
from app.crawler.service import CrawlerService
from app.crawler.sources import PREDEFINED_SOURCES
from sqlalchemy import select, func


# =====================================================================
# 题库模板 - 每个模板生成一个 True/False 题目
# 基于 AWS 公开文档中的知识点
# =====================================================================
QUESTION_TEMPLATES = [
    # ---------- EC2 / Compute ----------
    ("EC2", "Amazon EC2 provides resizable compute capacity in the cloud."),
    ("EC2", "EC2 supports On-Demand, Reserved, and Spot Instance pricing models."),
    ("EC2", "Reserved Instances provide a significant discount for 1-year or 3-year commitments."),
    ("EC2", "Spot Instances are suitable for stateless, fault-tolerant, and flexible workloads."),
    ("EC2", "Dedicated Hosts allow you to use your own server-bound software licenses."),
    ("EC2", "EC2 Auto Recovery automatically recovers an impaired instance."),
    ("EC2", "An instance store provides temporary block-level storage for EC2 instances."),
    ("EC2", "EBS volumes can be encrypted at rest using AWS KMS."),
    ("EC2", "EBS snapshots are stored in Amazon S3 and are incremental."),
    ("EC2", "You can modify an EBS volume type, size, or IOPS without downtime."),
    ("EC2", "Security groups act as a stateful firewall for EC2 instances."),
    ("EC2", "Security groups support only ALLOW rules, not DENY rules."),
    ("EC2", "Network ACLs are stateless and support both ALLOW and DENY rules."),
    ("EC2", "You can attach multiple security groups to a single EC2 instance."),
    ("EC2", "An Elastic IP address is a static public IPv4 address."),
    ("EC2", "Elastic IP addresses are free when they are associated with a running instance."),
    ("EC2", "You can change the instance type of a stopped EC2 instance."),
    ("EC2", "Instance metadata is accessible from within the instance at 169.254.169.254."),
    ("EC2", "User data scripts run with root privileges on Linux instances."),
    ("EC2", "Placement groups influence the placement of instances for performance."),
    ("EC2", "Cluster placement groups provide low-latency networking for HPC workloads."),
    ("EC2", "Spread placement groups support a maximum of 7 instances per AZ."),
    ("EC2", "Dedicated Instances run on hardware dedicated to a single customer."),
    ("EC2", "An Amazon Machine Image (AMI) provides the information required to launch an instance."),
    ("EC2", "Bare Metal instances provide direct access to the underlying processor."),
    ("Auto Scaling", "Auto Scaling automatically adjusts the number of EC2 instances based on demand."),
    ("Auto Scaling", "Auto Scaling can balance instances across multiple Availability Zones."),
    ("Auto Scaling", "Auto Scaling groups use launch templates to configure instances."),
    ("Auto Scaling", "Auto Scaling can replace unhealthy instances automatically."),
    ("ELB", "Elastic Load Balancing automatically distributes incoming traffic across targets."),
    ("ELB", "Application Load Balancer operates at Layer 7 and supports HTTP/HTTPS."),
    ("ELB", "Network Load Balancer operates at Layer 4 and handles millions of requests."),
    ("ELB", "Application Load Balancer supports path-based and host-based routing."),
    ("ELB", "Network Load Balancer supports static and elastic IP addresses."),
    ("ELB", "Classic Load Balancer is the legacy load balancer from AWS."),

    # ---------- Storage ----------
    ("S3", "Amazon S3 is a fully managed object storage service."),
    ("S3", "S3 provides 99.999999999% (11 9's) durability."),
    ("S3", "S3 Standard is designed for frequently accessed data."),
    ("S3", "S3 Standard-IA is for infrequently accessed data that needs rapid access."),
    ("S3", "S3 One Zone-IA stores data in a single Availability Zone."),
    ("S3", "S3 Glacier is a low-cost storage class for archival data."),
    ("S3", "S3 Glacier Deep Archive is the lowest-cost storage class."),
    ("S3", "S3 Intelligent-Tiering automatically optimizes storage costs."),
    ("S3", "S3 life cycle policies automate transitioning between storage classes."),
    ("S3", "S3 versioning protects against accidental deletion of objects."),
    ("S3", "S3 Transfer Acceleration speeds up uploads using edge locations."),
    ("S3", "S3 supports cross-origin resource sharing (CORS)."),
    ("S3", "S3 event notifications can trigger AWS Lambda functions."),
    ("S3", "S3 Object Lock prevents objects from being deleted or overwritten."),
    ("S3", "The maximum S3 object size is 5 TB."),
    ("S3", "S3 supports static website hosting."),
    ("EBS", "Amazon EBS provides block-level storage for EC2 instances."),
    ("EBS", "EBS volumes persist independently from the life of an instance."),
    ("EBS", "EBS supports gp3, io2, io1, st1, and sc1 volume types."),
    ("EBS", "EBS Multi-Attach allows a volume to be attached to multiple instances."),
    ("EFS", "Amazon EFS is a scalable file system for Linux workloads."),
    ("EFS", "EFS uses the NFS protocol and can scale to petabytes."),
    ("EFS", "EFS supports both Standard and Infrequent Access storage classes."),

    # ---------- VPC / Networking ----------
    ("VPC", "A VPC is a logically isolated virtual network in the AWS cloud."),
    ("VPC", "A VPC spans all Availability Zones in a region."),
    ("VPC", "A subnet spans a single Availability Zone."),
    ("VPC", "Each subnet must be associated with a route table."),
    ("VPC", "An Internet Gateway enables communication between a VPC and the internet."),
    ("VPC", "A NAT Gateway enables instances in a private subnet to access the internet."),
    ("VPC", "VPC Peering connects two VPCs using private IP addresses."),
    ("VPC", "VPC Peering does not support transitive routing."),
    ("VPC", "VPC Flow Logs capture information about IP traffic."),
    ("VPC", "AWS VPN enables secure connectivity between on-premises and AWS."),
    ("VPC", "AWS Direct Connect provides a dedicated private network connection."),
    ("VPC", "Transit Gateway connects multiple VPCs and on-premises networks."),
    ("VPC", "VPC Endpoints enable private connectivity to AWS services."),
    ("VPC", "Gateway Endpoints support S3 and DynamoDB."),
    ("VPC", "Interface Endpoints use Elastic Network Interfaces."),
    ("CloudFront", "Amazon CloudFront is a global content delivery network (CDN)."),
    ("CloudFront", "CloudFront supports custom SSL certificates."),
    ("CloudFront", "CloudFront can be used with Lambda@Edge for custom logic."),
    ("CloudFront", "CloudFront supports geo-restriction to block access by country."),
    ("Route53", "Amazon Route 53 is a DNS web service and domain registrar."),
    ("Route53", "Route 53 supports latency-based routing."),
    ("Route53", "Route 53 supports geolocation routing."),
    ("Route53", "Route 53 supports weighted routing."),
    ("Route53", "Route 53 supports failover routing with health checks."),
    ("Route53", "Route 53 alias records are free."),
    ("Route53", "Route 53 private hosted zones work within VPCs."),

    # ---------- Database ----------
    ("DynamoDB", "Amazon DynamoDB is a fully managed NoSQL database."),
    ("DynamoDB", "DynamoDB supports key-value and document data models."),
    ("DynamoDB", "DynamoDB offers single-digit millisecond performance at any scale."),
    ("DynamoDB", "DynamoDB supports eventually consistent reads by default."),
    ("DynamoDB", "DynamoDB Accelerator (DAX) is an in-memory cache."),
    ("DynamoDB", "DynamoDB auto scaling adjusts read and write capacity based on traffic."),
    ("DynamoDB", "DynamoDB Global Tables provide multi-region replication."),
    ("DynamoDB", "DynamoDB Streams capture item-level changes in near real-time."),
    ("DynamoDB", "DynamoDB supports transactions across multiple tables."),
    ("DynamoDB", "DynamoDB On-Demand mode charges per request with no capacity planning."),
    ("RDS", "Amazon RDS supports MySQL, PostgreSQL, MariaDB, Oracle, and SQL Server."),
    ("RDS", "RDS Multi-AZ provides automatic failover for high availability."),
    ("RDS", "RDS Read Replicas can be promoted to a standalone database."),
    ("RDS", "RDS Read Replicas can be in a different region."),
    ("RDS", "RDS supports automated backups with point-in-time recovery."),
    ("Aurora", "Amazon Aurora is compatible with MySQL and PostgreSQL."),
    ("Aurora", "Aurora automatically grows storage up to 128 TB."),
    ("Aurora", "Aurora provides 5x better performance than standard MySQL."),
    ("Redshift", "Amazon Redshift is a petabyte-scale data warehouse."),
    ("Redshift", "Redshift uses columnar storage for analytics performance."),
    ("Redshift", "Redshift Spectrum allows querying data directly in S3."),
    ("ElastiCache", "Amazon ElastiCache supports Redis and Memcached."),
    ("ElastiCache", "ElastiCache provides in-memory caching to improve application performance."),

    # ---------- Security ----------
    ("IAM", "AWS IAM manages users, groups, and roles."),
    ("IAM", "IAM policies are JSON documents that define permissions."),
    ("IAM", "IAM roles provide temporary credentials via AWS STS."),
    ("IAM", "The root account should be protected with MFA and not used daily."),
    ("IAM", "IAM Access Analyzer helps identify resources shared outside the account."),
    ("KMS", "AWS KMS is a managed service for creating and controlling encryption keys."),
    ("KMS", "KMS is integrated with over 100 AWS services."),
    ("KMS", "KMS supports automatic key rotation."),
    ("CloudTrail", "AWS CloudTrail records API activity for auditing purposes."),
    ("CloudTrail", "CloudTrail logs are stored in S3 and can be analyzed with Athena."),
    ("CloudTrail", "CloudTrail can be enabled across all regions."),
    ("Shield", "AWS Shield Standard provides automatic DDoS protection at no cost."),
    ("Shield", "AWS Shield Advanced provides enhanced DDoS protection and cost protection."),
    ("GuardDuty", "Amazon GuardDuty is a threat detection service using ML."),
    ("GuardDuty", "GuardDuty analyzes VPC Flow Logs, CloudTrail events, and DNS logs."),
    ("IAM", "AWS WAF protects web applications from SQL injection and XSS attacks."),
    ("CloudTrail", "AWS Config evaluates resource configurations against desired policies."),
    ("IAM", "AWS Organizations allows central governance of multiple accounts."),
    ("IAM", "Service Control Policies (SCPs) set permission guardrails in Organizations."),
    ("IAM", "AWS Artifact provides on-demand access to compliance reports."),

    # ---------- Serverless ----------
    ("Lambda", "AWS Lambda is a serverless compute service that runs code on demand."),
    ("Lambda", "Lambda supports Node.js, Python, Java, Go, Ruby, and .NET."),
    ("Lambda", "Lambda functions have a maximum execution timeout of 15 minutes."),
    ("Lambda", "Lambda is billed based on requests and compute duration."),
    ("Lambda", "Lambda can be triggered by S3 events, DynamoDB Streams, and API Gateway."),
    ("Lambda", "Lambda supports function URLs for direct HTTP access."),
    ("Lambda", "Lambda can access resources in a VPC."),
    ("Lambda", "Lambda supports container images up to 10 GB."),
    ("SQS", "Amazon SQS is a fully managed message queuing service."),
    ("SQS", "SQS supports standard queues and FIFO queues."),
    ("SQS", "SQS standard queues provide at-least-once delivery."),
    ("SQS", "SQS FIFO queues provide exactly-once processing."),
    ("SNS", "Amazon SNS is a fully managed pub/sub messaging service."),
    ("SNS", "SNS supports SMS, email, SQS, Lambda, and HTTP endpoints."),
    ("SNS", "SNS topics support fan-out to multiple subscribers."),
    ("Lambda", "Amazon API Gateway creates RESTful and WebSocket APIs."),
    ("Lambda", "API Gateway supports API versioning and throttling."),
    ("Lambda", "AWS Step Functions coordinates multiple Lambda functions as workflows."),
    ("Lambda", "Amazon EventBridge is a serverless event bus service."),

    # ---------- Containers ----------
    ("ECS", "Amazon ECS is a fully managed container orchestration service."),
    ("ECS", "ECS supports Fargate (serverless) and EC2 launch types."),
    ("ECS", "ECS tasks are the atomic unit of deployment in Amazon ECS."),
    ("ECS", "Amazon ECR is a fully managed container image registry."),
    ("EKS", "Amazon EKS runs Kubernetes clusters on AWS."),
    ("EKS", "EKS manages the Kubernetes control plane for you."),
    ("Fargate", "AWS Fargate is a serverless compute engine for containers."),
    ("Fargate", "Fargate eliminates the need to manage EC2 instances for containers."),

    # ---------- Well-Architected / Billing ----------
    ("EC2", "The AWS Well-Architected Framework has six pillars."),
    ("EC2", "The Reliability pillar includes automatic recovery from failure."),
    ("EC2", "The Security pillar focuses on protecting data and systems."),
    ("EC2", "The Cost Optimization pillar includes right-sizing resources."),
    ("EC2", "The Performance Efficiency pillar focuses on using resources efficiently."),
    ("EC2", "The Operational Excellence pillar includes operations as code."),
    ("EC2", "The Sustainability pillar focuses on environmental impact."),
    ("EC2", "AWS Trusted Advisor provides cost optimization and security checks."),
    ("EC2", "AWS Compute Optimizer recommends optimal instance types using ML."),
    ("EC2", "AWS Cost Explorer visualizes and analyzes spending."),
    ("EC2", "AWS Budgets send alerts when costs or usage exceed thresholds."),
    ("EC2", "The AWS Free Tier includes 750 hours of EC2 t2.micro per month."),
    ("EC2", "The AWS Pricing Calculator helps estimate monthly costs."),
    ("EC2", "AWS Savings Plans offer lower prices in exchange for usage commitment."),

    # ---------- AI/ML ----------
    ("SageMaker", "Amazon SageMaker is a fully managed machine learning platform."),
    ("SageMaker", "SageMaker supports training, tuning, and deploying ML models."),
    ("SageMaker", "SageMaker Studio is an integrated development environment for ML."),
    ("SageMaker", "SageMaker Ground Truth provides data labeling services."),
    ("SageMaker", "SageMaker can automatically tune model hyperparameters."),
    ("Rekognition", "Amazon Rekognition provides image and video analysis."),
    ("Rekognition", "Rekognition can detect objects, scenes, and faces."),
    ("Comprehend", "Amazon Comprehend is a natural language processing (NLP) service."),
    ("Comprehend", "Comprehend can extract entities, sentiment, and key phrases."),
    ("Polly", "Amazon Polly converts text into lifelike speech."),
    ("Polly", "Polly supports multiple languages and voices."),
    ("Comprehend", "Amazon Translate provides machine translation."),
    ("Lambda", "Amazon Transcribe converts speech to text using ASR."),
    ("Rekognition", "Amazon Textract extracts text and data from documents."),
    ("Comprehend", "Amazon Kendra is an intelligent enterprise search service."),
    ("SageMaker", "Amazon Forecast uses ML for time series forecasting."),
]


def crawl_faq(db):
    """爬取所有 AWS 官方 FAQ"""
    print("[Crawler] Starting FAQ crawl...")
    service = CrawlerService(db)
    total = 0
    for key in PREDEFINED_SOURCES:
        try:
            result = service.crawl_predefined_source(key, subject_id=1)
            total += result.imported
            print(f"  {key}: +{result.imported} new, {result.skipped} duplicates")
        except Exception as e:
            print(f"  {key}: FAILED - {e}")
    print(f"[Crawler] FAQ crawl complete. Total new questions: {total}\n")
    return total


def generate_questions(db, new_per_subject: int = 30):
    """基于模板生成题目，每个科目至少新增 new_per_subject 道"""
    print(f"[Generator] Starting question generation ({new_per_subject} per subject)...")
    admin = db.execute(select(User).where(User.email == "admin@cloudcert.com")).scalar_one()
    tags_map = {t.name: t.id for t in db.execute(select(Tag)).scalars().all()}
    subjects = list(db.execute(select(Subject)).scalars().all())

    total_new = 0
    total_skip = 0

    for subj in subjects:
        # 找出匹配该科目的模板
        subject_lower = subj.name.lower()
        matching = []
        for tag, content in QUESTION_TEMPLATES:
            if tag.lower() in subject_lower or subject_lower in tag.lower():
                matching.append((tag, content))
            # 补充：如果没有直接匹配，用通用匹配
        if not matching:
            for tag, content in QUESTION_TEMPLATES:
                if tag in ("EC2", "S3", "VPC", "IAM", "Lambda"):
                    matching.append((tag, content))

        # 随机打乱并取前 new_per_subject 道
        random.shuffle(matching)
        for tag, content in matching[:new_per_subject]:
            existing = db.execute(
                select(Question.id).where(Question.content.like(content[:50] + "%"))
            ).scalar_one_or_none()
            if existing:
                total_skip += 1
                continue

            # 随机对其中 20% 的内容反转（制造 False 题）
            is_true = random.random() > 0.2
            display_content = content
            if not is_true:
                # 对肯定句取反
                if content.startswith("Amazon") or content.startswith("AWS"):
                    display_content = content.replace(" provides", " does not provide")
                    if display_content == content:
                        display_content = content.replace(" supports", " does not support")
                else:
                    display_content = content  # 保持原样

            explanation = f"Statement: {content}\nAnswer: {'TRUE' if is_true else 'FALSE'}. " \
                          f"This is based on AWS public documentation."

            q = Question(
                subject_id=subj.id, question_type="single_choice", difficulty="medium",
                content=display_content, explanation=explanation,
                status="published", is_verified=True, created_by=admin.id,
            )
            db.add(q)
            db.flush()
            db.add(QuestionOption(question_id=q.id, option_key="A", content="True", is_correct=is_true, sort_order=0))
            db.add(QuestionOption(question_id=q.id, option_key="B", content="False", is_correct=not is_true, sort_order=1))
            if tag in tags_map:
                db.add(QuestionTag(question_id=q.id, tag_id=tags_map[tag]))
            total_new += 1

        db.flush()

    db.commit()
    print(f"[Generator] Complete. +{total_new} new, {total_skip} skipped (duplicates)\n")
    return total_new


def show_stats(db):
    """打印题库统计"""
    certs = db.execute(select(Certification)).scalars().all()
    print(f"\n{'='*60}")
    print(f"  CloudCert Pro - 题库统计 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print(f"{'='*60}")
    total_qs = 0
    for cert in certs:
        sub_ids = [s.id for s in db.execute(select(Subject).where(Subject.certification_id == cert.id)).scalars().all()]
        cnt = db.execute(select(func.count(Question.id)).where(Question.subject_id.in_(sub_ids))).scalar() or 0
        total_qs += cnt
        pct = min(100, round(cnt / cert.total_questions * 100)) if cert.total_questions else 0
        bar = "#" * (pct // 10) + "." * (10 - pct // 10)
        status = "OK" if cnt >= cert.total_questions else "SHORT"
        print(f"  [{status}] {bar} {cnt:4d}/{cert.total_questions} ({pct:3d}%) - {cert.name[:45]}")
    total = db.execute(select(func.count(Question.id))).scalar() or 0
    print(f"{'='*60}")
    print(f"  Total questions: {total} | Certification assigned: {total_qs}")
    print(f"  Generated from: AWS public documentation & FAQs")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="CloudCert Pro - Timed Question Generator")
    parser.add_argument("--all", action="store_true", help="Run all (crawl FAQ + generate 30/subject)")
    parser.add_argument("--crawl-faq", action="store_true", help="Crawl AWS FAQ pages only")
    parser.add_argument("--generate", type=int, nargs="?", const=30, help="Generate questions per subject")
    parser.add_argument("--stats", action="store_true", help="Show question statistics")
    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        return

    db = SessionLocal()
    try:
        if args.stats:
            show_stats(db)
            return

        if args.crawl_faq or args.all:
            crawl_faq(db)

        if args.generate is not None or args.all:
            count = args.generate if args.generate else 30
            generate_questions(db, new_per_subject=count)

        show_stats(db)
        print("  Done! New questions will appear in practice and exam modes.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
