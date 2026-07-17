"""Initialize seed data: certifications, subjects, tags, sample questions"""
from sqlalchemy import create_engine, select, func as sa_func
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.database import Base
from app.models.certification import Certification, Subject
from app.models.tag import Tag
from app.models.question import Question, QuestionOption, QuestionTag
from app.models.user import User
from app.models.knowledge import KnowledgeArticle, ArticleTag
from app.services.auth_service import AuthService

# Load question bank
import importlib.util as _util
_spec = _util.spec_from_file_location("question_bank", __file__.replace("seed_data.py", "question_bank.py"))
_qb_mod = _util.module_from_spec(_spec)
_spec.loader.exec_module(_qb_mod)
QUESTION_BANK = _qb_mod.QUESTION_BANK


settings = get_settings()
sync_url = settings.database_url.replace("+aiosqlite", "").replace("+asyncpg", "")
engine = create_engine(sync_url, connect_args={"check_same_thread": False} if "sqlite" in sync_url else {})
SessionLocal = sessionmaker(engine, expire_on_commit=False)


CERT_TAG_MAP = {
    # Map certification codes to question-bank tags
    "aws-saa": ["EC2", "S3", "VPC", "RDS", "DynamoDB", "IAM", "ELB", "Auto Scaling", "Lambda", "EFS", "EBS", "CloudFront", "Route53", "Aurora", "ElastiCache", "Redshift", "SNS", "SQS"],
    "aws-sap": ["EC2", "S3", "VPC", "RDS", "DynamoDB", "IAM", "ELB", "Auto Scaling", "Lambda", "EFS", "EBS", "CloudFront", "Route53", "KMS", "Redshift", "ElastiCache", "SQS"],
    "aws-dva": ["Lambda", "DynamoDB", "SQS", "SNS", "ECS", "EKS", "Fargate", "EC2", "S3", "ElastiCache", "RDS"],
    "aws-soa": ["EC2", "S3", "EBS", "VPC", "CloudTrail", "IAM", "Auto Scaling", "ELB", "Route53", "RDS"],
    "aws-clf": ["EC2", "S3", "RDS", "Lambda", "IAM", "VPC", "Auto Scaling", "DynamoDB", "ELB", "CloudFront"],
    "aws-dop": ["Lambda", "ECS", "EKS", "Fargate", "EC2", "S3", "IAM", "CloudTrail"],
    "aws-ans": ["VPC", "Route53", "CloudFront", "ELB", "NAT Gateway", "Security Group"],
    "aws-scs": ["IAM", "KMS", "CloudTrail", "Shield", "GuardDuty", "S3"],
    "aws-dbs": ["RDS", "DynamoDB", "Aurora", "Redshift", "ElastiCache", "S3"],
    "aws-saa-cn": ["EC2", "S3", "VPC", "RDS", "DynamoDB", "IAM", "ELB", "Auto Scaling", "Lambda", "EFS", "EBS"],
    "aws-sa": ["SageMaker", "Rekognition", "Comprehend", "Polly", "Lambda", "EC2", "S3", "DynamoDB"],
    "aws-mls": ["SageMaker", "Rekognition", "Comprehend", "Lambda", "EC2", "S3", "DynamoDB"],
    "aws-bd": ["Redshift", "S3", "DynamoDB", "RDS", "EC2"],
}

AWS_CERTIFICATIONS = [
    # (code, name, level, total_q, pass_score, duration_min, description, subjects)
    ("aws-saa", "AWS Solutions Architect Associate", "associate", 65, 720, 130,
     "Validate your ability to design distributed systems on AWS.", [
         ("Compute", 20), ("Storage", 15), ("Networking & Content Delivery", 18),
         ("Database", 14), ("Security & Compliance", 16), ("Architecture Design", 17),
     ]),
    ("aws-sap", "AWS Solutions Architect Professional", "professional", 75, 750, 180,
     "Validate advanced architecture skills for complex AWS solutions.", [
         ("Compute Design", 15), ("Storage Design", 12), ("Network Architecture", 15),
         ("Database Architecture", 13), ("Security Design", 15), ("Scalable Design", 15),
         ("Migration & Modernization", 15),
     ]),
    ("aws-dva", "AWS Developer Associate", "associate", 65, 720, 130,
     "Validate your ability to develop and maintain AWS-based applications.", [
         ("Development with AWS", 22), ("Security", 14), ("Deployment", 16),
         ("Troubleshooting & Optimization", 18), ("Serverless", 30),
     ]),
    ("aws-soa", "AWS SysOps Administrator Associate", "associate", 65, 720, 130,
     "Validate your ability to operate and manage workloads on AWS.", [
         ("Monitoring & Reporting", 15), ("Deployment & Provisioning", 14),
         ("Security & Compliance", 16), ("Networking", 14), ("Storage & Data Management", 12),
         ("Reliability & Business Continuity", 14), ("Automation & Optimization", 15),
     ]),
    ("aws-saa-cn", "AWS Solutions Architect Associate (Chinese)", "associate", 65, 720, 130,
     "Simplified Chinese version of the SAA exam.", [
         ("Compute", 20), ("Storage", 15), ("Networking & CDN", 18),
         ("Database", 14), ("Security & Compliance", 16), ("Architecture Design", 17),
     ]),
    ("aws-clf", "AWS Cloud Practitioner", "foundational", 65, 700, 90,
     "Validate foundational cloud knowledge and AWS services.", [
         ("Cloud Concepts", 26), ("Security & Compliance", 25), ("Technology", 33), ("Billing & Pricing", 16),
     ]),
    ("aws-dop", "AWS DevOps Engineer Professional", "professional", 75, 750, 180,
     "Validate expertise in provisioning and managing AWS infrastructure.", [
         ("SDLC Automation", 22), ("Configuration Management", 19),
         ("Monitoring & Logging", 15), ("Security & Governance", 15),
         ("Incident & Event Response", 14), ("High Availability & Scaling", 15),
     ]),
    ("aws-ans", "AWS Advanced Networking Specialty", "specialty", 65, 750, 170,
     "Validate advanced networking skills for AWS.", [
         ("Network Design", 30), ("Network Implementation", 20),
         ("Network Management", 20), ("Security & Compliance", 15), ("Hybrid IT", 15),
     ]),
    ("aws-scs", "AWS Security Specialty", "specialty", 65, 750, 170,
     "Validate expertise in AWS security services and best practices.", [
         ("Incident Response", 14), ("Logging & Monitoring", 15),
         ("Infrastructure Security", 20), ("Identity & Access Management", 20),
         ("Data Protection", 18), ("Compliance", 13),
     ]),
    ("aws-dbs", "AWS Database Specialty", "specialty", 65, 750, 170,
     "Validate expertise in AWS database services.", [
         ("Database Design", 26), ("Deployment & Migration", 20),
         ("Management & Operations", 18), ("Monitoring & Troubleshooting", 18),
         ("Database Security", 18),
     ]),
    ("aws-sa", "AWS Certified AI Practitioner", "foundational", 65, 700, 90,
     "Validate foundational AI/ML knowledge on AWS.", [
         ("AI/ML Fundamentals", 20), ("Amazon SageMaker", 25), ("AWS AI Services", 30),
         ("Security & Governance", 15), ("ML Best Practices", 10),
     ]),
    ("aws-mls", "AWS Machine Learning Specialty", "specialty", 65, 750, 170,
     "Validate expertise in ML/AI on AWS.", [
         ("Data Engineering", 20), ("Exploratory Data Analysis", 20),
         ("Modeling", 20), ("ML Implementation", 24), ("ML Security & Operations", 16),
     ]),
    ("aws-bd", "AWS Data Analytics Specialty", "specialty", 65, 750, 170,
     "Validate expertise in AWS data analytics services.", [
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


def seed():
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        # 1. Create admin
        admin = User(
            email="admin@cloudcert.com",
            password_hash=AuthService.hash_password("admin123"),
            nickname="Admin",
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.flush()

        # 2. Create tag tree
        tags_map = {}
        for cat_name, children in TAG_TREE.items():
            cat_tag = Tag(name=cat_name, full_path=cat_name, level=1)
            db.add(cat_tag)
            db.flush()
            tags_map[cat_name] = cat_tag
            for child_name, grandchildren in children.items():
                child_tag = Tag(
                    parent_id=cat_tag.id, name=child_name,
                    full_path=f"{cat_name} > {child_name}", level=2,
                )
                db.add(child_tag)
                db.flush()
                tags_map[child_name] = child_tag
                if grandchildren:
                    for g_name in grandchildren:
                        g_tag = Tag(
                            parent_id=child_tag.id, name=g_name,
                            full_path=f"{cat_name} > {child_name} > {g_name}", level=3,
                        )
                        db.add(g_tag)
                        db.flush()
                        tags_map[g_name] = g_tag

        # 3. Create certifications and subjects
        cert_map = {}
        for code, name, level, total_q, pass_score, duration_min, desc, subjects_data in AWS_CERTIFICATIONS:
            cert = Certification(
                provider="aws", code=code, name=name, level=level,
                description=desc, total_questions=total_q,
                pass_score=pass_score, duration_min=duration_min, is_active=True,
            )
            db.add(cert)
            db.flush()
            cert_map[code] = cert

            subjects = []
            for order, (sname, weight) in enumerate(subjects_data, 1):
                subj = Subject(certification_id=cert.id, name=sname, sort_order=order, weight=weight)
                db.add(subj)
                subjects.append(subj)
            db.flush()

            # Distribute questions from question bank — each question goes to ONE certification only
            assigned = 0
            allowed_tags = set(CERT_TAG_MAP.get(code, []))
            if not allowed_tags:
                # Fallback: try to match from subject names
                for subj in subjects:
                    allowed_tags.add(subj.name.lower().replace(" & ", " ").split()[0])

            for q_data in QUESTION_BANK:
                # Skip if already assigned to a previous cert
                existing = db.execute(
                    select(Question.id).where(Question.content.like(q_data["content"][:50] + "%"))
                ).scalar_one_or_none()
                if existing is not None:
                    continue

                # Find if any question tags match this cert's allowed tags
                q_tags = set(q_data.get("tags", []))
                matching_tags = q_tags & allowed_tags
                if not matching_tags:
                    continue  # No tag match for this certification

                # Find best subject for this question
                best_subj = subjects[0]
                for tag_name in matching_tags:
                    for subj in subjects:
                        sname = subj.name.lower()
                        if tag_name.lower() in sname or sname.split()[0].lower() in tag_name.lower():
                            best_subj = subj
                            break
                    else:
                        continue
                    break

                q = Question(
                    subject_id=best_subj.id, question_type=q_data.get("type", "single_choice"),
                    difficulty=q_data.get("difficulty", "medium"), content=q_data["content"],
                    explanation=q_data.get("explanation", ""), status="published",
                    is_verified=True, created_by=admin.id,
                )
                db.add(q)
                db.flush()

                for order, (key, content, is_correct) in enumerate(q_data["options"]):
                    db.add(QuestionOption(question_id=q.id, option_key=key, content=content, is_correct=is_correct, sort_order=order))

                for tag_name in q_data.get("tags", []):
                    resolved = tags_map.get(tag_name)
                    if not resolved:
                        resolved = next((t for t in tags_map.values() if t.full_path == tag_name), None)
                    if resolved and not db.execute(
                        select(QuestionTag.id).where(
                            QuestionTag.question_id == q.id, QuestionTag.tag_id == resolved.id
                        )
                    ).scalar_one_or_none():
                        db.add(QuestionTag(question_id=q.id, tag_id=resolved.id))
                assigned += 1
            db.flush()

        # 4. Knowledge articles
        articles = [
            {
                "provider": "aws", "category": "compute",
                "title": "Amazon EC2 Complete Guide",
                "summary": "EC2 instance types, pricing models, and security groups.",
                "content": "Amazon EC2 is AWS's core compute service.\n\n## Instance Types\n- General Purpose: t3, m5\n- Compute Optimized: c5\n- Memory Optimized: r5\n- Storage Optimized: i3\n\n## Pricing Models\n1. On-Demand: pay per hour/second\n2. Reserved Instances:预付获取折扣\n3. Spot Instances: use spare capacity\n\n## Security Groups\nVirtual firewall for instance traffic.",
                "tags": ["EC2"],
            },
            {
                "provider": "aws", "category": "storage",
                "title": "Amazon S3 Storage Classes Deep Dive",
                "summary": "Standard, IA, Glacier, Deep Archive use cases.",
                "content": "Amazon S3 offers multiple storage classes.\n\n## Storage Classes\n1. S3 Standard: frequent access\n2. S3 Intelligent-Tiering: auto-optimize\n3. S3 Standard-IA: infrequent access\n4. S3 One Zone-IA: single AZ\n5. S3 Glacier: archive\n6. S3 Glacier Deep Archive: long-term",
                "tags": ["S3"],
            },
            {
                "provider": "aws", "category": "network",
                "title": "VPC Network Architecture Best Practices",
                "summary": "Subnet design, route tables, NAT Gateway, VPC Peering.",
                "content": "Amazon VPC lets you provision a logically isolated network.\n\n## Core Components\n- VPC: virtual private cloud\n- Subnets: public and private\n- Route Tables: control traffic\n- Internet Gateway: public access\n- NAT Gateway: private outbound\n- VPC Peering: connect VPCs",
                "tags": ["VPC"],
            },
        ]

        for art_data in articles:
            article = KnowledgeArticle(
                provider=art_data["provider"], category=art_data["category"],
                title=art_data["title"], summary=art_data["summary"],
                content=art_data["content"], status="published",
                created_by=admin.id,
            )
            db.add(article)
            db.flush()
            for tag_name in art_data["tags"]:
                if tag_name in tags_map:
                    db.add(ArticleTag(article_id=article.id, tag_id=tags_map[tag_name].id))

        db.commit()

        cert_count = len(AWS_CERTIFICATIONS)
        q_count = db.execute(select(sa_func.count(Question.id))).scalar() or 0
        print(f"Seed data imported successfully!")
        print(f"  Admin account: admin@cloudcert.com / admin123")
        print(f"  Certifications: {cert_count} AWS certs")
        print(f"  Tags: {len(tags_map)} tags")
        print(f"  Questions: {q_count} across all certifications")
        print(f"  Knowledge articles: {len(articles)}")


if __name__ == "__main__":
    seed()
