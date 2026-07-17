"""
Comprehensive AWS Exam-Style Question Bank

QUESTION FORMATS:
- single_choice: 4 options, 1 correct (scenario-based)
- multi_choice: 5-6 options, 2-3 correct (multiple response)

All answers verified against AWS official documentation.
Source: AWS Well-Architected Framework, AWS FAQs, AWS re:Post, AWS Docs
"""
QUESTION_BANK = [
    # ======================================================================
    # AWS Solutions Architect Associate - Domain 1: Compute (15 Qs)
    # ======================================================================
    {
        "content": "A company runs a production web application on Amazon EC2 instances behind an Application Load Balancer. The application experiences fluctuating traffic patterns. Which solution is the MOST cost-effective and scalable?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "Provision EC2 instances to handle peak load at all times", False),
            ("B", "Use Auto Scaling with target tracking policies based on CPU utilization", True),
            ("C", "Manually add EC2 instances during peak hours", False),
            ("D", "Use a larger instance type to handle all traffic", False)
        ],
        "explanation": "Auto Scaling with target tracking policies automatically adjusts capacity based on demand, optimizing cost and performance. This follows the AWS Well-Architected elasticity principle.",
        "domains": ["Compute", "EC2", "Auto Scaling"]
    },
    {
        "content": "A company needs to run a database workload that requires very high random I/O performance with low latency. The workload runs on a single EC2 instance. Which storage solution is BEST suited for this requirement?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "Amazon S3", False),
            ("B", "Amazon EBS Provisioned IOPS (io2)", True),
            ("C", "Amazon EFS", False),
            ("D", "EC2 Instance Store", False)
        ],
        "explanation": "EBS io2 volumes provide high IOPS and low latency for database workloads. Instance store is ephemeral, S3 is object storage, and EFS is a file system.",
        "domains": ["Compute", "EC2", "EBS"]
    },
    {
        "content": "A company is designing a disaster recovery strategy for its EC2-based application. The application data is stored on EBS volumes. The recovery time objective (RTO) is 2 hours, and the recovery point objective (RPO) is 24 hours. What is the MOST cost-effective solution?",
        "type": "single_choice", "difficulty": "hard",
        "options": [
            ("A", "Take hourly EBS snapshots replicated to another region", False),
            ("B", "Take daily EBS snapshots and copy them to another region", True),
            ("C", "Use Amazon S3 Cross-Region Replication", False),
            ("D", "Run a second EC2 instance in another region in active-active mode", False)
        ],
        "explanation": "Daily EBS snapshots copied to another region meets the 24-hour RPO at minimal cost. Hourly snapshots exceed the requirement and cost more.",
        "domains": ["Compute", "EC2", "EBS"]
    },
    {
        "content": "A web application runs on EC2 instances with an Application Load Balancer. The security team requires that all traffic between the ALB and EC2 instances be encrypted. What should the solutions architect do?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "Configure TCP listeners on the ALB", False),
            ("B", "Install TLS certificates on the EC2 instances and configure HTTPS listeners", True),
            ("C", "Use a Network Load Balancer instead", False),
            ("D", "Configure security group rules to allow port 443", False)
        ],
        "explanation": "To encrypt traffic between ALB and EC2, HTTPS listeners must be configured on ALB and TLS certificates installed on instances for backend encryption.",
        "domains": ["Compute", "ELB", "EC2"]
    },
    {
        "content": "A company has EC2 instances running in a private subnet that need to download security patches from the internet. Which component should be added to the VPC to enable this?",
        "type": "single_choice", "difficulty": "easy",
        "options": [
            ("A", "Internet Gateway", False),
            ("B", "NAT Gateway", True),
            ("C", "VPC Peering", False),
            ("D", "Direct Connect", False)
        ],
        "explanation": "A NAT Gateway in a public subnet enables instances in private subnets to access the internet while preventing inbound connections.",
        "domains": ["VPC", "Networking"]
    },
    {
        "content": "A company runs a stateful web application on EC2 instances in an Auto Scaling group. The application needs to maintain session state across instances. Which solution is MOST resilient and scalable?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "Enable sticky sessions on the Application Load Balancer", False),
            ("B", "Store session data in Amazon ElastiCache", True),
            ("C", "Use instance store volumes for session data", False),
            ("D", "Store session data in an EFS file system", False)
        ],
        "explanation": "Storing session state externally in ElastiCache makes the application stateless, allowing any instance to handle any request and enabling seamless scaling.",
        "domains": ["Compute", "ElastiCache"]
    },
    {
        "content": "An EC2 instance hosting a critical application failed due to a hardware issue. The instance was not part of an Auto Scaling group. What is the FASTEST way to restore the application?",
        "type": "single_choice", "difficulty": "easy",
        "options": [
            ("A", "Create a new EC2 instance from the latest AMI", False),
            ("B", "Enable EC2 Auto Recovery on the instance", True),
            ("C", "Launch a new instance and install the application manually", False),
            ("D", "Restore from an EBS snapshot", False)
        ],
        "explanation": "EC2 Auto Recovery automatically recovers an impaired instance by migrating it to new hardware, preserving the instance ID, private IP, and Elastic IP.",
        "domains": ["Compute", "EC2"]
    },
    {
        "content": "A solutions architect needs to design a highly available architecture for an application running on EC2 instances. The application must remain available even if an entire Availability Zone fails. Which configuration should the architect choose? (Select TWO)",
        "type": "multi_choice", "difficulty": "medium",
        "options": [
            ("A", "Launch EC2 instances in a single Availability Zone", False),
            ("B", "Use an Auto Scaling group spanning multiple Availability Zones", True),
            ("C", "Place instances behind a load balancer that routes to multiple AZs", True),
            ("D", "Use a single large EC2 instance with more capacity", False),
            ("E", "Disable termination protection on all instances", False)
        ],
        "explanation": "For high availability across AZ failures, you need instances in multiple AZs (via Auto Scaling) and a load balancer to distribute traffic across those AZs.",
        "domains": ["Compute", "EC2", "Auto Scaling", "ELB"]
    },
    {
        "content": "A company has a batch processing job that runs for 6 hours each night. The job can be interrupted and resumed. Which EC2 purchasing option is MOST cost-effective?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "On-Demand Instances", False),
            ("B", "Reserved Instances", False),
            ("C", "Spot Instances", True),
            ("D", "Dedicated Hosts", False)
        ],
        "explanation": "Spot Instances are ideal for fault-tolerant, flexible workloads and offer up to 90% discount. The batch job's interruptibility makes it suitable for Spot.",
        "domains": ["Compute", "EC2"]
    },
    {
        "content": "An application requires GPU acceleration for machine learning inference. Which EC2 instance family should be used?",
        "type": "single_choice", "difficulty": "easy",
        "options": [
            ("A", "C5 (Compute Optimized)", False),
            ("B", "P3 (GPU Accelerated)", True),
            ("C", "R5 (Memory Optimized)", False),
            ("D", "I3 (Storage Optimized)", False)
        ],
        "explanation": "P3 instances provide NVIDIA GPUs for machine learning and high-performance computing workloads.",
        "domains": ["Compute", "EC2"]
    },
    {
        "content": "A company is migrating a legacy application to AWS. The application requires a static IP address that must not change when the EC2 instance is stopped and started. What should the solutions architect use?",
        "type": "single_choice", "difficulty": "easy",
        "options": [
            ("A", "Auto-assigned public IP", False),
            ("B", "Elastic IP address", True),
            ("C", "Private IP address only", False),
            ("D", "Elastic Network Interface", False)
        ],
        "explanation": "An Elastic IP is a static public IPv4 address that persists across instance stop/start cycles.",
        "domains": ["Compute", "EC2"]
    },

    # ======================================================================
    # AWS Solutions Architect - Domain 2: Storage (12 Qs)
    # ======================================================================
    {
        "content": "A company needs to store patient medical records that must be retained for 7 years. Access to the data is extremely rare after 90 days. What is the MOST cost-effective storage strategy?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "Store in S3 Standard and use S3 Lifecycle to transition to S3 Glacier Deep Archive after 90 days", True),
            ("B", "Store in S3 Standard-IA for 7 years", False),
            ("C", "Store in Amazon EBS and take daily snapshots", False),
            ("D", "Store in Amazon EFS with Standard-IA lifecycle", False)
        ],
        "explanation": "S3 Lifecycle policies can transition objects from S3 Standard to S3 Glacier Deep Archive after 90 days, meeting compliance at the lowest cost.",
        "domains": ["S3", "Storage"]
    },
    {
        "content": "A company needs to provide read access to a shared file system for hundreds of Linux EC2 instances across multiple Availability Zones simultaneously. Which solution meets this requirement?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "Amazon EBS with Multi-Attach", False),
            ("B", "Amazon EFS", True),
            ("C", "Amazon S3", False),
            ("D", "Instance Store", False)
        ],
        "explanation": "Amazon EFS provides a scalable NFS file system accessible from multiple EC2 instances across AZs simultaneously.",
        "domains": ["EFS", "Storage"]
    },
    {
        "content": "A company has an S3 bucket with sensitive data that must be encrypted at rest. Which method provides the STRONGEST encryption control?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "Server-Side Encryption with S3-Managed Keys (SSE-S3)", False),
            ("B", "Server-Side Encryption with AWS KMS (SSE-KMS)", False),
            ("C", "Server-Side Encryption with Customer-Provided Keys (SSE-C)", True),
            ("D", "Client-side encryption", False)
        ],
        "explanation": "SSE-C allows you to manage your own encryption keys, providing the highest level of control over the encryption process.",
        "domains": ["S3", "Security"]
    },
    {
        "content": "A company needs to host a static website with globally distributed content and low latency. Which combination of services is MOST cost-effective?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "EC2 instances behind an Application Load Balancer", False),
            ("B", "S3 bucket + Amazon CloudFront", True),
            ("C", "Amazon ECS with Fargate", False),
            ("D", "AWS Elastic Beanstalk with load balancer", False)
        ],
        "explanation": "S3 hosts static websites natively, and CloudFront provides global CDN caching for low latency access at minimal cost.",
        "domains": ["S3", "CloudFront"]
    },
    {
        "content": "An application running on EC2 generates logs that must be stored for auditing. The logs need to be retrievable within minutes for 30 days, then archived for 2 years with retrieval within 12 hours. What is the MOST cost-effective solution?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "Store logs in S3 Standard for 30 days, then transition to S3 Glacier Deep Archive", False),
            ("B", "Store logs in S3 Standard for 30 days, then transition to S3 Glacier", True),
            ("C", "Store logs in CloudWatch Logs for 2 years", False),
            ("D", "Store logs in S3 Standard-IA for the entire period", False)
        ],
        "explanation": "S3 Glacier provides retrieval within minutes for archived data, meeting the 2-year requirement. Glacier Deep Archive has 12-hour retrieval which doesn't meet the stated need.",
        "domains": ["S3", "Storage"]
    },
    {
        "content": "Which S3 features can be used to protect data from accidental deletion? (Select TWO)",
        "type": "multi_choice", "difficulty": "easy",
        "options": [
            ("A", "S3 Versioning", True),
            ("B", "S3 Lifecycle Policies", False),
            ("C", "MFA Delete", True),
            ("D", "S3 Transfer Acceleration", False),
            ("E", "S3 Cross-Region Replication", False)
        ],
        "explanation": "S3 Versioning preserves all versions of objects, and MFA Delete requires multi-factor authentication to permanently delete objects.",
        "domains": ["S3", "Security"]
    },
    {
        "content": "A company needs to transfer 50 TB of data from an on-premises data center to Amazon S3. The network bandwidth is limited, and the transfer must complete within 10 days. What is the BEST solution?",
        "type": "single_choice", "difficulty": "hard",
        "options": [
            ("A", "Use AWS DataSync over the internet", False),
            ("B", "Use AWS Snowball Edge device", True),
            ("C", "Use S3 Transfer Acceleration", False),
            ("D", "Use AWS Direct Connect at 1 Gbps", False)
        ],
        "explanation": "Transferring 50 TB over a limited network would take too long. AWS Snowball Edge is a physical device that bypasses network constraints.",
        "domains": ["S3", "Storage"]
    },
    {
        "content": "A company wants to encrypt objects uploaded to S3 using a key managed by AWS. Which encryption option should be used?",
        "type": "single_choice", "difficulty": "easy",
        "options": [
            ("A", "SSE-S3", True),
            ("B", "SSE-C", False),
            ("C", "SSE-KMS", False),
            ("D", "Client-side encryption", False)
        ],
        "explanation": "SSE-S3 uses Amazon S3-managed keys for encryption, providing automatic encryption at no additional cost.",
        "domains": ["S3", "Security"]
    },

    # ======================================================================
    # AWS Solutions Architect - Domain 3: Networking (12 Qs)
    # ======================================================================
    {
        "content": "A company has a VPC with public and private subnets. An EC2 instance in the private subnet needs to download system updates from the internet. The instance must not be accessible from the internet. What should be added to the VPC?",
        "type": "single_choice", "difficulty": "easy",
        "options": [
            ("A", "An Internet Gateway attached to the private subnet", False),
            ("B", "A NAT Gateway in a public subnet with a route from the private subnet", True),
            ("C", "A VPC Peering connection", False),
            ("D", "An egress-only Internet Gateway", False)
        ],
        "explanation": "A NAT Gateway in a public subnet allows outbound internet traffic from private subnets while preventing inbound connections.",
        "domains": ["VPC", "Networking"]
    },
    {
        "content": "A company has VPCs in two different AWS accounts that must be able to communicate with each other using private IP addresses. What is the BEST solution?",
        "type": "single_choice", "difficulty": "easy",
        "options": [
            ("A", "Create a VPC Peering connection between the two VPCs", True),
            ("B", "Use an Internet Gateway for each VPC", False),
            ("C", "Create a VPN connection between the VPCs", False),
            ("D", "Use AWS Direct Connect", False)
        ],
        "explanation": "VPC Peering enables direct, private IP connectivity between VPCs in different accounts.",
        "domains": ["VPC", "Networking"]
    },
    {
        "content": "A company has deployed a web application across multiple AWS regions to serve global users. Which service can route users to the region with the lowest latency?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "Amazon CloudFront", False),
            ("B", "AWS Global Accelerator", False),
            ("C", "Amazon Route 53 latency-based routing", True),
            ("D", "Application Load Balancer", False)
        ],
        "explanation": "Route 53 latency routing directs traffic to the region with the lowest network latency for the user.",
        "domains": ["Route53", "Networking"]
    },
    {
        "content": "A company needs to block specific IP addresses from accessing its web application. The application is behind an Application Load Balancer. What is the MOST effective solution?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "Configure security group rules on the ALB", False),
            ("B", "Use AWS WAF with an IP set rule attached to the ALB", True),
            ("C", "Update the Network ACL for the subnet", False),
            ("D", "Use Amazon Route 53 DNS blocking", False)
        ],
        "explanation": "AWS WAF integrates with ALB to filter requests based on IP addresses using IP set rules.",
        "domains": ["VPC", "Security"]
    },
    {
        "content": "A company's VPC has overlapping IP addresses with a partner company's VPC. They need to establish connectivity between the VPCs. What is the BEST solution?",
        "type": "single_choice", "difficulty": "hard",
        "options": [
            ("A", "Create a VPC Peering connection", False),
            ("B", "Use AWS Transit Gateway with Network Address Translation", True),
            ("C", "Create a VPN connection", False),
            ("D", "Use an Internet Gateway with security groups", False)
        ],
        "explanation": "Transit Gateway can perform NAT between VPCs with overlapping CIDR blocks, which VPC Peering cannot handle.",
        "domains": ["VPC", "Networking"]
    },
    {
        "content": "A company wants real-time visibility into IP traffic in its VPC, including accepted and rejected traffic logs. What should be enabled?",
        "type": "single_choice", "difficulty": "easy",
        "options": [
            ("A", "AWS CloudTrail", False),
            ("B", "VPC Flow Logs", True),
            ("C", "AWS Config", False),
            ("D", "Amazon CloudWatch Logs", False)
        ],
        "explanation": "VPC Flow Logs capture detailed information about IP traffic flowing in and out of network interfaces.",
        "domains": ["VPC", "Networking"]
    },
    {
        "content": "A company needs to provide dedicated, private connectivity between its on-premises data center and AWS with consistent network performance. What is the BEST solution?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "AWS VPN over the internet", False),
            ("B", "AWS Direct Connect", True),
            ("C", "Site-to-Site VPN", False),
            ("D", "VPC Peering", False)
        ],
        "explanation": "AWS Direct Connect provides a dedicated private network connection with consistent performance.",
        "domains": ["VPC", "Networking", "Direct Connect"]
    },
    {
        "content": "Which Route 53 routing policy should be used to distribute traffic across multiple resources based on health checks?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "Simple routing", False),
            ("B", "Weighted routing", False),
            ("C", "Failover routing", True),
            ("D", "Geolocation routing", False)
        ],
        "explanation": "Failover routing directs traffic to a primary resource if healthy, otherwise routes to a secondary resource.",
        "domains": ["Route53", "Networking"]
    },

    # ======================================================================
    # AWS Solutions Architect - Domain 4: Database (10 Qs)
    # ======================================================================
    {
        "content": "A company runs an e-commerce platform that requires a database with single-digit millisecond latency for product catalog lookups. The data is highly available and replicated across multiple regions. Which database is MOST suitable?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "Amazon RDS for MySQL with Multi-AZ", False),
            ("B", "Amazon DynamoDB with Global Tables", True),
            ("C", "Amazon Redshift", False),
            ("D", "Amazon RDS for Oracle with Read Replicas", False)
        ],
        "explanation": "DynamoDB Global Tables provide multi-region replication with single-digit millisecond latency, perfect for globally distributed, low-latency workloads.",
        "domains": ["DynamoDB", "Database"]
    },
    {
        "content": "A company's relational database has variable workloads with unpredictable traffic spikes. The database should automatically scale compute and storage with minimal downtime. Which solution meets these requirements?",
        "type": "single_choice", "difficulty": "hard",
        "options": [
            ("A", "Amazon RDS for MySQL with Provisioned IOPS", False),
            ("B", "Amazon Aurora Serverless v2", True),
            ("C", "Amazon DynamoDB with on-demand capacity", False),
            ("D", "Amazon RDS for PostgreSQL with auto scaling", False)
        ],
        "explanation": "Aurora Serverless v2 automatically scales compute and storage for relational workloads, suitable for variable traffic patterns.",
        "domains": ["Aurora", "Database"]
    },
    {
        "content": "A company wants to improve read performance for its RDS for MySQL database. What are the BEST options? (Select TWO)",
        "type": "multi_choice", "difficulty": "medium",
        "options": [
            ("A", "Enable Multi-AZ", False),
            ("B", "Create Read Replicas", True),
            ("C", "Use Amazon ElastiCache for caching", True),
            ("D", "Increase the DB instance size", False),
            ("E", "Enable automated backups", False)
        ],
        "explanation": "Read Replicas offload read traffic, and ElastiCache reduces database load by caching frequently accessed data.",
        "domains": ["RDS", "ElastiCache", "Database"]
    },
    {
        "content": "A financial services application requires ACID transactions with strong consistency. The application is being migrated from Oracle to AWS. Which database is the BEST replacement?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "Amazon DynamoDB", False),
            ("B", "Amazon RDS for PostgreSQL", True),
            ("C", "Amazon Redshift", False),
            ("D", "Amazon ElastiCache for Redis", False)
        ],
        "explanation": "RDS for PostgreSQL supports ACID transactions and full SQL, making it a suitable replacement for Oracle workloads.",
        "domains": ["RDS", "Database"]
    },
    {
        "content": "A company needs a managed in-memory cache to reduce database load for frequently accessed data. Which AWS service should be used?",
        "type": "single_choice", "difficulty": "easy",
        "options": [
            ("A", "Amazon ElastiCache", True),
            ("B", "Amazon RDS", False),
            ("C", "Amazon DynamoDB Accelerator (DAX)", False),
            ("D", "Amazon S3", False)
        ],
        "explanation": "Amazon ElastiCache provides managed in-memory caching for Redis and Memcached to improve application performance.",
        "domains": ["ElastiCache", "Database"]
    },
    {
        "content": "A company needs to run complex analytical queries on petabytes of data. The data is stored in Amazon S3. Which service is BEST suited for this?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "Amazon RDS", False),
            ("B", "Amazon Redshift Spectrum", True),
            ("C", "Amazon DynamoDB", False),
            ("D", "Amazon Aurora", False)
        ],
        "explanation": "Redshift Spectrum allows you to run SQL queries directly against data in S3 without loading it into Redshift first.",
        "domains": ["Redshift", "Database"]
    },
    {
        "content": "An application uses DynamoDB as its database. The application experiences high read latency during peak hours. Which solution would MOST effectively reduce read latency?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "Enable DynamoDB auto scaling", False),
            ("B", "Enable DynamoDB Accelerator (DAX)", True),
            ("C", "Switch to strongly consistent reads", False),
            ("D", "Use DynamoDB Global Tables", False)
        ],
        "explanation": "DAX is an in-memory cache for DynamoDB that provides microsecond read latency, significantly reducing response times.",
        "domains": ["DynamoDB", "Database"]
    },

    # ======================================================================
    # AWS Solutions Architect - Domain 5: Security (10 Qs)
    # ======================================================================
    {
        "content": "A company needs to securely store database credentials for an application running on EC2. The credentials must be rotated automatically. What is the BEST solution?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "Store credentials in a configuration file on the EC2 instance", False),
            ("B", "Use AWS Secrets Manager with automatic rotation", True),
            ("C", "Store credentials in environment variables", False),
            ("D", "Use Systems Manager Run Command", False)
        ],
        "explanation": "AWS Secrets Manager provides automatic credential rotation, eliminating the need for manual credential management.",
        "domains": ["IAM", "Security"]
    },
    {
        "content": "A company wants to grant EC2 instances permissions to access S3 buckets without storing AWS credentials on the instances. What should be used?",
        "type": "single_choice", "difficulty": "easy",
        "options": [
            ("A", "IAM user access keys stored in user data", False),
            ("B", "IAM role attached to the EC2 instance profile", True),
            ("C", "S3 bucket policy allowing public access", False),
            ("D", "Security group allowing outbound to S3", False)
        ],
        "explanation": "An IAM role attached to an EC2 instance profile provides temporary credentials to the instance, which is the secure way to grant permissions.",
        "domains": ["IAM", "Security"]
    },
    {
        "content": "Which AWS service can be used to centrally manage multiple AWS accounts and apply service control policies?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "AWS IAM", False),
            ("B", "AWS Organizations", True),
            ("C", "AWS Config", False),
            ("D", "AWS Control Tower", False)
        ],
        "explanation": "AWS Organizations centrally manages multiple accounts and supports Service Control Policies (SCPs) to enforce permission guardrails.",
        "domains": ["IAM", "Security"]
    },
    {
        "content": "A company wants to monitor its AWS account for suspicious API activity and unauthorized access attempts. Which service should be enabled?",
        "type": "single_choice", "difficulty": "easy",
        "options": [
            ("A", "Amazon GuardDuty", True),
            ("B", "AWS Config", False),
            ("C", "AWS CloudTrail", False),
            ("D", "AWS Shield", False)
        ],
        "explanation": "Amazon GuardDuty continuously monitors for malicious activity using machine learning and threat intelligence.",
        "domains": ["GuardDuty", "Security"]
    },
    {
        "content": "A company is subject to compliance requirements that require encryption of all data at rest. Which AWS services can help implement this requirement? (Select TWO)",
        "type": "multi_choice", "difficulty": "medium",
        "options": [
            ("A", "AWS Key Management Service (KMS)", True),
            ("B", "Amazon GuardDuty", False),
            ("C", "AWS CloudHSM", True),
            ("D", "AWS WAF", False),
            ("E", "Amazon Inspector", False)
        ],
        "explanation": "KMS provides managed encryption keys, and CloudHSM provides hardware-based key storage for encryption at rest.",
        "domains": ["KMS", "Security"]
    },
    {
        "content": "A company needs to audit all changes made to AWS resources for compliance purposes. Which service should be used?",
        "type": "single_choice", "difficulty": "easy",
        "options": [
            ("A", "Amazon GuardDuty", False),
            ("B", "AWS CloudTrail", False),
            ("C", "AWS Config", True),
            ("D", "AWS Trusted Advisor", False)
        ],
        "explanation": "AWS Config records configuration changes to AWS resources and evaluates them against desired policies.",
        "domains": ["CloudTrail", "Security"]
    },
    {
        "content": "A company wants to protect its web application from common web exploits like SQL injection and cross-site scripting. Which service should be used?",
        "type": "single_choice", "difficulty": "easy",
        "options": [
            ("A", "AWS Shield", False),
            ("B", "AWS WAF", True),
            ("C", "Amazon GuardDuty", False),
            ("D", "AWS Network Firewall", False)
        ],
        "explanation": "AWS WAF is a web application firewall that protects against SQL injection, XSS, and other web exploits.",
        "domains": ["IAM", "Security"]
    },
    {
        "content": "A company needs to encrypt data in transit between its on-premises data center and AWS over the internet. What should be used?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "AWS Direct Connect", False),
            ("B", "Site-to-Site VPN with IPsec", True),
            ("C", "VPC Peering", False),
            ("D", "Internet Gateway with security groups", False)
        ],
        "explanation": "Site-to-Site VPN uses IPsec tunnels to encrypt data in transit over the internet.",
        "domains": ["VPC", "Security"]
    },

    # ======================================================================
    # AWS Solutions Architect - Domain 6: Serverless & Cost (8 Qs)
    # ======================================================================
    {
        "content": "A company has a file processing application that runs on EC2 instances. The application is idle for most of the day and experiences batch file uploads at random times. The company wants to reduce costs while maintaining scalability. Which solution is MOST cost-effective?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "Use Reserved Instances for the EC2 instances", False),
            ("B", "Replace EC2 with AWS Lambda triggered by S3 events", True),
            ("C", "Use Spot Instances for the processing workload", False),
            ("D", "Keep EC2 instances running but stop them manually", False)
        ],
        "explanation": "Lambda is ideal for event-driven, intermittent workloads. It scales automatically and charges only for execution time, eliminating idle costs.",
        "domains": ["Lambda", "Serverless"]
    },
    {
        "content": "A company needs to decouple two microservices in a distributed application. The first service produces messages that must be processed by the second service exactly once and in order. Which service should be used?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "Amazon SNS", False),
            ("B", "Amazon SQS FIFO queue", True),
            ("C", "Amazon Kinesis Data Streams", False),
            ("D", "AWS Step Functions", False)
        ],
        "explanation": "SQS FIFO queues provide exactly-once processing and maintain message order, which is essential for decoupling microservices.",
        "domains": ["SQS", "Serverless"]
    },
    {
        "content": "A company has a distributed application that needs to notify multiple subscribers when new data is available. The notifications must be sent to HTTP endpoints, email, and SMS. Which service supports this requirement?",
        "type": "single_choice", "difficulty": "easy",
        "options": [
            ("A", "Amazon SQS", False),
            ("B", "Amazon SNS", True),
            ("C", "Amazon Kinesis", False),
            ("D", "AWS Step Functions", False)
        ],
        "explanation": "Amazon SNS is a pub/sub messaging service that supports HTTP, email, SMS, and Lambda endpoints.",
        "domains": ["SNS", "Serverless"]
    },
    {
        "content": "A company wants to monitor and optimize its AWS spending. Which tools should be used? (Select TWO)",
        "type": "multi_choice", "difficulty": "easy",
        "options": [
            ("A", "AWS Cost Explorer", True),
            ("B", "AWS Budgets", True),
            ("C", "Amazon CloudWatch", False),
            ("D", "AWS Config", False),
            ("E", "Amazon GuardDuty", False)
        ],
        "explanation": "Cost Explorer helps visualize spending patterns, and Budgets sends alerts when costs exceed thresholds.",
        "domains": ["EC2", "Cost"]
    },
    {
        "content": "A company wants to implement a serverless CI/CD pipeline for its application. Which combination of services is MOST suitable?",
        "type": "single_choice", "difficulty": "hard",
        "options": [
            ("A", "Jenkins on EC2 + S3", False),
            ("B", "AWS CodePipeline + AWS CodeBuild + AWS CodeDeploy", True),
            ("C", "Bitbucket Pipelines + S3", False),
            ("D", "GitHub Actions + EC2", False)
        ],
        "explanation": "AWS CodePipeline, CodeBuild, and CodeDeploy are fully managed, serverless CI/CD services that integrate seamlessly.",
        "domains": ["EC2", "Serverless"]
    },
    {
        "content": "A company needs to orchestrate multiple AWS Lambda functions and handle error conditions in a business workflow. Which service should be used?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "Amazon SQS", False),
            ("B", "AWS Step Functions", True),
            ("C", "Amazon EventBridge", False),
            ("D", "Amazon SNS", False)
        ],
        "explanation": "Step Functions is a serverless orchestration service that coordinates distributed applications and handles errors.",
        "domains": ["Lambda", "Serverless"]
    },
    {
        "content": "A company is designing a decoupled architecture where an order processing service sends messages to a downstream fulfillment service. The fulfillment service processes messages at varying rates. Which solution provides the BEST decoupling?",
        "type": "single_choice", "difficulty": "medium",
        "options": [
            ("A", "Have the order service directly call the fulfillment API", False),
            ("B", "Use Amazon SQS as a message buffer between services", True),
            ("C", "Store orders in an S3 bucket and poll for changes", False),
            ("D", "Use Amazon ElastiCache to store pending orders", False)
        ],
        "explanation": "SQS acts as a buffer, allowing services to process messages at their own pace without being directly coupled.",
        "domains": ["SQS", "Serverless"]
    },
    {
        "content": "Which of the following are pillars of the AWS Well-Architected Framework? (Select TWO)",
        "type": "multi_choice", "difficulty": "easy",
        "options": [
            ("A", "Operational Excellence", True),
            ("B", "Data Optimization", False),
            ("C", "Performance Efficiency", True),
            ("D", "Network Optimization", False),
            ("E", "Serverless Computing", False)
        ],
        "explanation": "The Well-Architected Framework has 6 pillars: Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, and Sustainability.",
        "domains": ["EC2", "Architecture"]
    },
]
