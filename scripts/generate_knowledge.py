# -*- coding: utf-8 -*-
"""
CloudCert Pro - 知识文章生成器
生成丰富的云认证知识文章，全部内容为中文，保留专业服务名词英文。
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import argparse
from datetime import datetime
from app.database import SessionLocal
from app.models.user import User
from app.crawler.knowledge_importer import KnowledgeImporter, KnowledgeArticleData
from sqlalchemy import select, func
from app.models.knowledge import KnowledgeArticle


KNOWLEDGE_ARTICLES = {

"compute": [

KnowledgeArticleData(
provider="aws", category="compute",
title="Amazon EC2 详解：实例类型、定价模型与最佳实践",
summary="全面了解 Amazon EC2 的实例类型（通用型、计算优化型、内存优化型、存储优化型、GPU 型）、五种定价模式（按需、预留实例、Spot 实例、专用主机、Savings Plans），以及安全组、弹性 IP、用户数据等核心功能的最佳实践。",
source_url="https://aws.amazon.com/ec2/faqs/",
tags=["EC2", "Compute"],
content="""## 1. EC2 实例类型总览

Amazon EC2 (Elastic Compute Cloud) 是 AWS 的核心计算服务，提供可伸缩的虚拟服务器。实例按用途分为以下大类：

### 通用型 (General Purpose)
- t4g/t3/t2：突发性能实例，适合开发测试、微服务、低流量 Web 服务器
- m7g/m6i/m5：计算、内存、网络资源均衡，适合应用服务器、游戏服务器

### 计算优化型 (Compute Optimized)
- c7g/c6i/c5：提供最高性价比的计算资源
- 适用场景：批处理、高性能 Web 服务器、科学建模、广告投放

### 内存优化型 (Memory Optimized)
- r7g/r6i/r5：适用于内存密集型工作负载
- x2iedn/x1e：最高 4TB 内存，适合 SAP HANA、内存数据库
- z1d：高频率处理器加大内存组合

### 存储优化型 (Storage Optimized)
- i4i/i3：高随机 I/O 性能，适合 NoSQL 数据库（MongoDB、Cassandra、Elasticsearch）
- d2/d3：高顺序磁盘吞吐，适合 HDFS、MapReduce

### 加速计算型 (GPU/FPGA)
- p4d/p3：NVIDIA GPU，用于机器学习训练、HPC
- g5/g4dn：GPU 用于图形渲染、视频转码、ML 推理
- inf1/inf2：AWS Inferentia 芯片，专为 ML 推理优化
- trn1/trn2：AWS Trainium 芯片，专为 ML 训练优化

## 2. 五种定价模式

### 按需 (On-Demand)
- 按秒计费（最少 60 秒），无需预付
- 适合：短期不可预测工作负载、首次迁移测试、开发环境

### 预留实例 (Reserved Instances)
- 1 年或 3 年承诺，全预付/部分预付/无预付
- 折扣：最高 72%（3 年全预付）
- 类型：Standard（固定配置）、Convertible（可转换实例类型）
- 适合：稳定状态工作负载（数据库、企业应用）

### Spot 实例 (Spot Instances)
- 最高 90% 折扣，2 分钟回收通知
- 适合：容错、无状态、弹性工作负载（大数据、CI/CD、渲染）
- 最佳实践：结合 Spot Fleet 跨多个实例类型和可用区使用

### 专用主机 (Dedicated Hosts)
- 物理服务器完全独享
- 适用场景：自带许可 (BYOL)、合规性要求、服务器绑定软件许可证

### Savings Plans
- 承诺每小时消费金额（1 年或 3 年）
- 折扣类似 RI，最高 72%
- 类型：Compute Savings Plans（最灵活）、EC2 Instance Savings Plans
- 覆盖 EC2 + Fargate + Lambda

## 3. 核心功能

### 安全组 (Security Groups) 与网络 ACL 对比
- 安全组：有状态，仅支持 Allow 规则，实例级别
- 网络 ACL：无状态，同时支持 Allow 和 Deny，子网级别

### 弹性 IP (Elastic IP)
- 静态公网 IPv4 地址，可与实例动态关联/解绑
- 未关联运行实例时产生费用
- 每个区域默认 5 个，可申请提升

### 用户数据 (User Data)
- 实例首次启动时自动执行脚本（最高 16KB）
- Linux：以 root 权限执行；Windows：以 Administrator 权限执行

### 实例元数据 (Instance Metadata)
- 访问地址：http://169.254.169.254/latest/meta-data/
- 获取实例 ID、AMI ID、可用区、本地 IP 等信息
- IMDSv2 要求使用 PUT 请求获取 Token
"""
),

KnowledgeArticleData(
provider="aws", category="compute",
title="AWS Lambda 深度解析：无服务器计算完全指南",
summary="深入了解 AWS Lambda 的运行机制、触发方式（同步/异步/流式）、并发模型（预留并发、预置并发）、冷启动优化策略、VPC 集成方案以及常见无服务器架构模式。",
source_url="https://aws.amazon.com/lambda/faqs/",
tags=["Lambda", "Serverless", "Compute"],
content="""## 1. Lambda 基本概念

AWS Lambda 是事件驱动的无服务器计算服务，无需预置或管理服务器即可运行代码。

### 关键限制
- 执行超时：最长 900 秒（15 分钟）
- 临时存储：512 MB - 10,240 MB（/tmp 目录）
- 函数包大小：压缩后 50 MB（直接上传），250 MB（S3 引用）
- 并发执行：每个账户默认 1000（可申请提升）
- 容器镜像：最大 10 GB

### 支持的运行时
- 托管运行时：Node.js 20/18、Python 3.12/3.11/3.10/3.9、Java 21/17/11/8、Go 1.x、Ruby 3.2、.NET 8
- 自定义运行时：通过 Runtime API 支持任何 Linux 兼容语言
- 容器镜像：支持符合 OCI 标准的镜像

## 2. 触发方式

### 同步调用（直接返回结果）
- API Gateway REST/HTTP API
- Lambda Function URL
- Application Load Balancer
- Amazon Cognito 事件

### 异步调用（队列缓冲加重试）
- S3 事件通知（PutObject、DeleteObject 等）
- SNS 主题通知
- EventBridge（CloudWatch Events）

### 流式调用（数据源轮询）
- DynamoDB Streams
- Kinesis Data Streams
- SQS 队列

## 3. 并发模型

### 预留并发 (Reserved Concurrency)
- 为函数预留固定数量的并发实例
- 同时限制该函数的最大并发数

### 预置并发 (Provisioned Concurrency)
- 提前初始化指定数量的执行环境
- 消除冷启动延迟，适用于延迟敏感应用
- 会产生额外费用（环境预热）

### 冷启动优化策略
1. 减少包体积，使用 Lambda Layers
2. 通过定时 CloudWatch Events 保持实例活跃
3. 选择较快运行时（Python/Node.js 快于 Java/.NET）
4. 使用 SnapStart（Java）缩短冷启动至约 200ms
5. 关键路径使用预置并发

## 4. VPC 集成

将 Lambda 附加到 VPC 子网和安全组，通过 ENI（弹性网络接口）进行网络连接。
- 使用 RDS Proxy 管理数据库连接池
- 考虑使用 ElastiCache Serverless 或 DAX
- 将 Lambda 放在私有子网中，通过 NAT 访问公网

## 5. 性能优化

### 内存配置：128 MB - 10,240 MB
- CPU 比例：每 1,769 MB 分配 1 vCPU
- 为 CPU 密集型任务分配更多内存

### 连接复用
- 在函数外部初始化数据库连接、HTTP 客户端
- 利用执行环境缓存（全局变量在调用间保留）
- 使用连接池（boto3 自动连接复用）

## 6. 常见架构模式

### REST API 后端
```
API Gateway -> Lambda(业务逻辑) -> DynamoDB
                   |                   |
              Lambda(认证)          DAX 缓存
```

### 事件驱动处理
```
S3 上传 -> Lambda(验证/压缩) -> S3(处理后) -> Lambda(分析) -> DynamoDB
```
"""
),

KnowledgeArticleData(
provider="aws", category="compute",
title="Auto Scaling 完整指南：弹性伸缩策略与实践",
summary="深入解析 AWS Auto Scaling 的扩缩容策略（目标追踪、步进调整、计划扩缩容、预测扩缩容）、健康检查机制、生命周期钩子以及跨可用区部署的最佳实践。",
source_url="https://aws.amazon.com/autoscaling/faqs/",
tags=["Auto Scaling", "Compute"],
content="""## 1. 核心概念

Auto Scaling 自动调整计算资源数量以匹配应用需求。

### 核心组件
- 启动模板 (Launch Template)：定义实例配置（AMI、实例类型、安全组）
- Auto Scaling 组：管理实例组的逻辑容器
- 扩缩容策略：决定何时增加或减少实例

### 基本工作流程
1. 定义启动模板
2. 创建 Auto Scaling 组（设置最小/最大/期望容量）
3. 配置扩缩容策略
4. Auto Scaling 自动维持期望容量

## 2. 扩缩容策略类型

### 动态扩缩容
1. 目标追踪 (Target Tracking)：基于指标自动调整，如维持 CPU 在 70%
2. 步进调整 (Step Scaling)：根据偏离程度逐步调整
3. 简单调整 (Simple Scaling)：单次调整到指定容量

### 计划扩缩容 (Scheduled Scaling)
- 基于时间表，如工作日早 9 点扩容
- 适用于已知的流量模式

### 预测扩缩容 (Predictive Scaling)
- 使用机器学习分析历史流量模式
- 提前预置资源应对预期负载
- 需要至少 24 小时的历史数据

## 3. 健康检查

### 检查类型
- EC2 检查：实例状态（运行中/停止/终止）
- ELB 检查：负载均衡健康检查（HTTP 响应码）
- 自定义健康检查

### 不健康实例处理
- 自动终止并替换
- 配合生命周期钩子进行优雅关闭
- 记录到 CloudWatch 日志

## 4. 最佳实践
1. 跨 2-3 个可用区部署
2. 使用 Application Load Balancer 分发流量
3. 配置冷却时间，避免频繁扩缩容震荡
4. 混合使用 Spot 和 On-Demand 实例降低成本
5. 使用 Warm Pools 减少冷启动时间
"""
),
],

"storage": [

KnowledgeArticleData(
provider="aws", category="storage",
title="Amazon S3 完全手册：存储类、安全防护与生命周期管理",
summary="全面解读 Amazon S3 的存储类（Standard、Standard-IA、Glacier、Glacier Deep Archive）、数据保护机制（版本控制、Object Lock、复制）、生命周期策略、访问控制（Bucket Policy、IAM、预签名 URL）以及性能优化方案。",
source_url="https://aws.amazon.com/s3/faqs/",
tags=["S3", "Storage"],
content="""## 1. 核心概念

Amazon S3 提供 99.999999999% 的持久性（11 个 9）。

### 基础概念
- 对象 (Object)：基本存储单元，最大 5TB
- 存储桶 (Bucket)：对象的逻辑容器，全局唯一名称
- 键 (Key)：对象的唯一标识符（路径）
- 区域 (Region)：数据存储在所选区域

## 2. 存储类详解

### 热存储层
| 存储类 | 可用性 | 适用场景 | 最短存储期 |
|--------|--------|---------|-----------|
| S3 Standard | 99.99% | 频繁访问数据 | 无 |
| S3 Express One Zone | 99.5% | 单可用区低延迟 | 无 |

### 低频存储层
| 存储类 | 可用性 | 适用场景 | 最短存储期 |
|--------|--------|---------|-----------|
| S3 Standard-IA | 99.9% | 低频访问但需快速读取 | 30 天 |
| S3 One Zone-IA | 99.5% | 可重建的低频数据 | 30 天 |

### 归档存储层
| 存储类 | 恢复时间 | 最短存储期 |
|--------|---------|-----------|
| S3 Glacier | 1-5 分钟（加急）到 5-12 小时（标准） | 90 天 |
| S3 Glacier Deep Archive | 12 小时（标准）到 48 小时（批量） | 180 天 |

## 3. 数据保护

### 版本控制 (Versioning)
- 保留对象的所有版本，包括删除标记
- 可恢复意外删除或覆盖的对象
- 与生命周期策略配合管理版本成本

### 对象锁定 (Object Lock)
- WORM 模式：写入一次，多次读取
- 保留期限：指定日期或无限期
- 法律封存 (Legal Hold)：用户设置后不可移除

### 复制 (Replication)
- CRR（跨区域复制）：灾难恢复、合规性
- SRR（同区域复制）：日志聚合、数据冗余
- 支持实时复制和历史复制

## 4. 访问控制

### 权限策略层次
1. 存储桶策略 (Bucket Policy)：JSON 格式的访问控制
2. IAM 策略：附加到用户或角色的权限
3. 预签名 URL：临时授权访问，最长 7 天

### Block Public Access
- 四层公网访问阻止（账户级别和桶级别）

## 5. 性能优化

### 上传优化
- 分片上传 (Multipart Upload)：大于 100MB 建议使用
- S3 Transfer Acceleration：利用边缘节点加速上传

### 查询优化
- S3 Select：在服务端过滤数据，减少传输量
- Athena：直接在 S3 上运行 SQL 查询
"""
),

KnowledgeArticleData(
provider="aws", category="storage",
title="Amazon EBS 弹性块存储深度指南",
summary="详解 EBS 卷类型（gp3、io2 Block Express、st1、sc1）、快照管理（增量备份、生命周期策略）、KMS 加密机制、性能优化以及 RAID 配置等高级功能。",
source_url="https://aws.amazon.com/ebs/faqs/",
tags=["EBS", "Storage"],
content="""## 1. EBS 概述

Amazon EBS (Elastic Block Store) 为 EC2 实例提供持久块级存储。

### 关键特性
- 持久性：独立于实例生命周期
- 加密：AES-256 通过 KMS 实现
- 快照：增量备份到 S3
- 弹性：在线修改卷类型、大小、IOPS，无需停机

## 2. 卷类型对比

### SSD 类型
| 类型 | 最大 IOPS | 最大吞吐 | 适用场景 |
|------|----------|---------|---------|
| gp3 | 16,000 | 1,000 MB/s | 通用工作负载 |
| io2 Block Express | 256,000 | 4,000 MB/s | 关键数据库（SAP HANA、Oracle） |
| io1 | 64,000 | 1,000 MB/s | 传统高 IOPS 工作负载 |

### HDD 类型
| 类型 | 最大吞吐 | 适用场景 |
|------|---------|---------|
| st1 | 500 MB/s | 大数据、日志处理 |
| sc1 | 250 MB/s | 冷数据归档 |

## 3. 快照管理
- 增量备份（仅保存变更块）
- 存储在 S3（11 个 9 持久性）
- 支持跨区域复制、跨账户共享
- 生命周期策略自动创建和删除

## 4. 加密
- 基于 KMS 的 AES-256 加密
- 对性能无影响
- 加密快照自动产生加密卷
- 可在区域级别启用默认加密
"""
),
],

"network": [

KnowledgeArticleData(
provider="aws", category="network",
title="Amazon VPC 网络架构深度解析",
summary="全面讲解 VPC 子网设计（3-AZ 推荐架构）、路由表配置、NAT 网关、VPC Peering、Transit Gateway、Direct Connect、VPN、VPC Endpoints（Gateway/Interface）以及 VPC Flow Logs 的最佳实践。",
source_url="https://aws.amazon.com/vpc/faqs/",
tags=["VPC", "Network"],
content="""## 1. VPC 核心概念

Amazon VPC (Virtual Private Cloud) 是 AWS 云中逻辑隔离的虚拟网络。

### 核心组件
- CIDR 块：IP 地址范围（最大 /16，最小 /28）
- 子网 (Subnet)：位于一个可用区内的 IP 地址段
- 路由表 (Route Table)：控制子网的流量路由
- 互联网网关 (IGW)：VPC 到互联网的通信
- NAT 网关：私有子网访问互联网

### CIDR 规划最佳实践
1. 为每个环境（开发/测试/生产）分配独立 CIDR
2. 为区域间互联预留不重叠的 CIDR
3. 使用 RFC 1918 私有地址（10.0.0.0/8、172.16.0.0/12、192.168.0.0/16）
4. 为每个可用区分配 /20 子网

## 2. 推荐的三可用区架构

```
VPC: 10.0.0.0/16
  可用区 A：公网 /24（ALB、NAT）、私网应用 /24（EC2、ECS）、私网数据 /24（RDS、缓存）
  可用区 B：相同结构
  可用区 C：相同结构
```

## 3. 路由配置

常见路由规则：
- 本地路由：10.0.0.0/16 -> local（自动添加）
- 互联网：0.0.0.0/0 -> igw-xxx（公网子网）
- NAT：0.0.0.0/0 -> nat-xxx（私网子网）
- 对等连接：172.16.0.0/16 -> pcx-xxx
- VPN：10.0.0.0/8 -> vgw-xxx

## 4. 连接选项

### VPC Peering
- 直接连接两个 VPC，不经过互联网
- 不支持传递路由 (transitive peering)
- 支持跨区域和跨账户

### Transit Gateway
- 中心辐射架构，连接数千个 VPC
- 支持传递路由 (transitive routing)
- 集成 VPN 和 Direct Connect

### Direct Connect
- 专用物理连接（1-100 Gbps）
- 一致的网络性能，较低的带宽成本
- BGP 路由

### VPN
- 加密的互联网隧道
- 快速部署
- 可作为 Direct Connect 的备份

## 5. 安全组与网络 ACL 对比

| 特性 | 安全组 (Security Group) | 网络 ACL (NACL) |
|------|------------------------|-----------------|
| 状态 | 有状态 | 无状态 |
| 规则 | 仅 Allow | Allow + Deny |
| 层级 | 实例级别 | 子网级别 |
| 评估 | 所有规则同时评估 | 按编号顺序 |

## 6. VPC Endpoints

### Gateway Endpoints（免费）
- 支持 S3 和 DynamoDB
- 通过路由表实现，无需 NAT

### Interface Endpoints（PrivateLink，按小时计费）
- 支持 100 多种 AWS 服务
- 通过 ENI 实现

## 7. VPC Flow Logs
- 捕获 IP 流量元数据
- 支持 VPC、子网、ENI 级别
- 目标：CloudWatch Logs 或 S3
"""
),

KnowledgeArticleData(
provider="aws", category="network",
title="Amazon CloudFront CDN 内容分发网络指南",
summary="深入了解 CloudFront 的全球 450+ 边缘节点架构、缓存策略（TTL、缓存键）、安全加速（SSL/TLS、WAF、DDoS 防护）、边缘计算（CloudFront Functions、Lambda@Edge）和实时监控。",
source_url="https://aws.amazon.com/cloudfront/faqs/",
tags=["CloudFront", "Network", "CDN"],
content="""## 1. CloudFront 简介

Amazon CloudFront 是高速内容分发网络 (CDN)，在全球拥有 450+ 个边缘节点。

### 核心优势
- 低延迟：全球 450+ 节点就近服务用户
- 高吞吐：Tbps 级别聚合带宽
- 安全：内置 AWS Shield Standard DDoS 防护
- 可编程：CloudFront Functions 和 Lambda@Edge

## 2. 源站选项
- S3 存储桶（配合 Origin Access Control 保护）
- Application Load Balancer
- 自定义 HTTP 源站
- AWS Media Services
- 可配置多个源站实现故障转移

## 3. 缓存策略

### 缓存键设置
- 默认：URL 路径 + 查询参数（可选）
- Cookies：全部/白名单/无
- Headers：白名单（如 Accept-Language）

### TTL 设置：0 秒到 365 天
- 基于 Cache-Control 和 Expires 请求头

## 4. 安全功能

### 访问控制
- AWS WAF 集成（SQL 注入、XSS 防护）
- 地理限制（白名单/黑名单国家）
- 签名 URL 和签名 Cookie (Signed URLs/Cookies)
- Origin Access Control (OAC) 保护 S3 源站

### SSL/TLS
- 自定义 SSL 证书（通过 ACM）
- 支持 SNI 和专用 IP
- 可配置最低 TLS 版本

## 5. 边缘计算

### CloudFront Functions（轻量级）
- JavaScript 运行时，亚毫秒级执行
- 适合 URL 重写、请求头操作

### Lambda@Edge（全功能）
- Python/Node.js 运行时，最长 30 秒
- 可访问外部服务（DynamoDB、S3）
"""
),
],

"database": [

KnowledgeArticleData(
provider="aws", category="database",
title="Amazon RDS 关系型数据库服务完整指南",
summary="全面介绍 Amazon RDS 支持的数据库引擎（MySQL、PostgreSQL、SQL Server、Oracle、MariaDB、Aurora）、高可用架构（Multi-AZ、Multi-AZ DB Cluster）、只读副本（Read Replicas）、备份恢复策略和性能监控。",
source_url="https://aws.amazon.com/rds/faqs/",
tags=["RDS", "Database"],
content="""## 1. RDS 概述

Amazon RDS (Relational Database Service) 是托管的关系型数据库服务。

### 支持的引擎
- Amazon Aurora（兼容 MySQL 和 PostgreSQL）
- MySQL 5.7、8.0
- PostgreSQL 14-16
- SQL Server 2016-2022
- Oracle 19c、21c
- MariaDB 10.5-10.11

### 托管优势
- 自动软件补丁
- 自动备份（最多保留 35 天）
- 自动故障检测和恢复
- 自动存储扩展
- 监控和性能指标

## 2. 高可用架构

### Multi-AZ（多可用区部署）
- 自动同步备用副本到不同可用区
- 自动故障转移，通常小于 60 秒
- 对应用层完全透明

### Multi-AZ DB Cluster（集群模式）
- 1 个主节点 + 2 个可读备用节点
- 加速故障转移，小于 35 秒
- 读流量可分发到备用节点

## 3. 只读副本 (Read Replicas)
- 异步复制，最多 15 个副本
- 支持跨区域复制
- 可提升为主库
- 减轻主库读取压力

## 4. 备份与恢复

### 自动备份
- 每日快照 + 每 5 分钟事务日志备份
- 保留期 1-35 天
- 支持时间点恢复 (PITR)

### 手动快照
- 用户手动触发，不限保留时间
- 支持跨账户共享和跨区域复制

## 5. 监控与优化
- 关键指标：CPU 利用率、数据库连接数、IOPS、复制延迟、存储空间
- Performance Insights：等待事件分析、SQL 级别性能分析
- Optimized Insights：可操作的建议
"""
),

KnowledgeArticleData(
provider="aws", category="database",
title="Amazon DynamoDB NoSQL 数据库完全指南",
summary="深入讲解 DynamoDB 的数据模型（表、项、属性）、主键设计（分区键、排序键）、二级索引（LSI、GSI）、读写容量模式（按需/预置）、一致性模型、DynamoDB Streams、Global Tables 和 DAX 缓存加速。",
source_url="https://aws.amazon.com/dynamodb/faqs/",
tags=["DynamoDB", "Database"],
content="""## 1. DynamoDB 概述

Amazon DynamoDB 是全托管 NoSQL 键值数据库和文档数据库。

### 核心特性
- 任意规模下个位数毫秒延迟
- 自动扩缩容，无需停机
- 无服务器，零管理
- 多可用区自动复制，高持久性
- 支持跨表 ACID 事务

## 2. 数据模型

### 表结构
- 表 (Table)：数据的集合
- 项 (Item)：表中的一行，无 schema 约束
- 属性 (Attribute)：项中的字段
- 主键：
  - 分区键 (Partition Key)：单一键
  - 复合键 (Partition Key + Sort Key)：分区键加排序键

### 主键设计最佳实践
1. 选择高基数分区键，确保请求均匀分布
2. 避免热分区，单个分区键请求过多
3. 使用 Sort Key 实现范围查询（时间序列、排序）
4. 复合键设计：如 PK = UserID，SK = OrderDate

## 3. 索引

### 本地二级索引 (LSI)
- 相同分区键，不同排序键
- 创建表时必须指定
- 支持强一致性读取
- 每表最多 5 个

### 全局二级索引 (GSI)
- 不同分区键和排序键
- 表创建后可添加
- 仅支持最终一致性
- 每表最多 20 个（可提升）

## 4. 读写容量模式

### 按需模式 (On-Demand)
- 自动扩缩容，按请求付费
- 适合不可预测的工作负载

### 预置模式 (Provisioned)
- 指定 RCU/WCU，可使用 Auto Scaling
- 大规模使用成本更低
- 适合可预测的工作负载

### RCU/WCU 计算
- 1 RCU = 1 次强一致性 4KB 读取，或 2 次最终一致性 4KB 读取
- 1 WCU = 1 次 1KB 写入

## 5. 高级功能

### DynamoDB Streams
- 捕获项级别变更（增删改）
- 保留 24 小时
- 触发 Lambda 函数
- 用于实时分析、索引同步、数据复制

### DAX (DynamoDB Accelerator)
- 内存缓存，微秒级延迟
- 兼容现有 API，对应用透明
- 自动缓存失效

### Global Tables（全局表）
- 多主复制，支持多区域
- 冲突解决：最后写入者获胜
- 可在任何区域读写
"""
),
],

"security": [

KnowledgeArticleData(
provider="aws", category="security",
title="AWS IAM 身份与访问管理权威指南",
summary="全面讲解 IAM 用户、组、角色、策略的核心概念，安全最佳实践（MFA、最小权限、权限边界）、IAM Access Analyzer、STS 临时凭证、SCP 服务控制策略以及跨账户访问方案。",
source_url="https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html",
tags=["IAM", "Security"],
content="""## 1. 核心概念

### 组件
- 用户 (User)：代表个人或服务账号
- 组 (Group)：用户的集合，简化权限管理
- 角色 (Role)：授予 AWS 服务或临时权限
- 策略 (Policy)：JSON 权限文档，定义 Allow 或 Deny

### 策略示例
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:GetObject"],
    "Resource": ["arn:aws:s3:::my-bucket/*"]
  }]
}
```

## 2. 五种认证方式
1. 用户名/密码：登录 AWS 管理控制台
2. 访问密钥 (Access Key + Secret Key)：CLI/SDK 使用
3. 多因素认证 (MFA)：额外安全层
4. 临时凭证：通过 AWS STS 获取安全令牌
5. 联合身份：SAML/OIDC 集成外部身份提供商

## 3. 安全最佳实践

### 根账户保护
- 启用 MFA，不创建访问密钥
- 避免日常使用，仅限于账户管理操作

### 最小权限原则
- 初始权限为 Deny All，仅授予必需权限
- 使用条件语句限制范围（来源 IP、时间、MFA）
- 定期审查未使用的权限和策略

### 权限边界 (Permissions Boundary)
- 对 IAM 实体设置最大权限上限
- 适用于跨账户管理场景

## 4. 服务控制策略 (SCP)
- 在 AWS Organizations 中使用
- 设置账户级权限上限
- 支持白名单和黑名单策略
- 不影响管理账户

## 5. IAM Access Analyzer
- 自动识别对外共享的资源
- 分析 S3 存储桶策略、KMS 密钥、IAM 角色
- 生成最小权限策略建议

## 6. 跨账户访问

### 角色切换方式
1. 账户 A 创建信任策略，允许账户 B 的 IAM 用户承担
2. 账户 B 创建权限策略，定义可访问的资源
3. 账户 B 用户调用 AssumeRole API 获取临时凭证

### 基于资源的策略
- S3 Bucket Policy、SQS Queue Policy、KMS Key Policy 可直接授权跨账户访问
"""
),
],

"ai": [

KnowledgeArticleData(
provider="aws", category="ai",
title="Amazon SageMaker 机器学习平台完整指南",
summary="全面介绍 SageMaker 的机器学习全生命周期：数据准备（Ground Truth）、模型构建（Studio Notebooks）、训练（Training Jobs）、自动调优（Hyperparameter Tuning）、部署（实时/批量/Serverless 推理）和模型监控（Model Monitor）。",
source_url="https://docs.aws.amazon.com/sagemaker/latest/dg/whatis.html",
tags=["SageMaker", "AI/ML"],
content="""## 1. SageMaker 概述

Amazon SageMaker 是全托管机器学习平台，覆盖机器学习的完整生命周期。

### ML 流水线
数据准备 (Ground Truth) -> 模型构建 (Studio Notebooks) -> 训练 (Training Jobs) -> 调优 (Hyperparameter Tuning) -> 部署 (Endpoint) -> 监控 (Model Monitor)

## 2. 核心组件

### SageMaker Studio
- 基于 JupyterLab 的集成开发环境
- 集成代码编写、实验跟踪、可视化
- 支持团队协作和共享

### 训练选项
- 内置算法：XGBoost、Linear Learner、Object2Vec 等
- 自定义容器：支持 TensorFlow、PyTorch、Hugging Face
- 托管训练，按使用量付费
- 分布式训练，自动分区和并行化

### 自动模型调优 (Hyperparameter Tuning)
- 贝叶斯优化搜索
- 自动并行训练作业
- 目标最大化准确率或最小化损失

## 3. SageMaker Autopilot
- 自动机器学习 (AutoML)
- 自动数据预处理
- 自动算法选择
- 生成候选模型并排序

## 4. 推理部署

### 实时推理
- 托管端点 (Real-time Endpoint)
- 自动扩缩容
- 支持 A/B 测试

### 批量推理 (Batch Transform)
- 自动分片处理
- 自动选择最优实例

### 无服务器推理 (Serverless Inference)
- 自动扩缩容到零
- 按请求计费

## 5. 模型监控 (Model Monitor)
- 数据漂移检测：输入数据分布变化
- 模型质量监控：准确率变化
- 偏差检测：公平性分析
- 自动告警

## 6. Ground Truth（数据标注）
- 自动标注（基于现有模型）
- 人工标注（通过 Mechanical Turk 或第三方）
- 标注工作流管理和质量评估
"""
),
],
}


def main():
    parser = argparse.ArgumentParser(description="CloudCert Pro - 知识文章生成器")
    parser.add_argument("--all", action="store_true", help="生成所有知识文章")
    parser.add_argument("--stats", action="store_true", help="查看知识库统计")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.stats:
            show_stats(db)
            return

        if args.all:
            admin = db.execute(select(User).where(User.email == "admin@cloudcert.com")).scalar_one()
            importer = KnowledgeImporter(db, created_by=admin.id)
            all_articles = []
            for cat_articles in KNOWLEDGE_ARTICLES.values():
                all_articles.extend(cat_articles)
            result = importer.import_articles(all_articles)
            print(f"总计: {result.total}, 新增: {result.imported}, 跳过(重复): {result.skipped}, 失败: {result.failed}")

        show_stats(db)
    finally:
        db.close()


def show_stats(db):
    total = db.execute(select(func.count(KnowledgeArticle.id))).scalar() or 0
    print(f"\n知识库统计")
    print(f"  总文章数: {total}")
    print(f"  运行 --all 生成/导入文章")


if __name__ == "__main__":
    main()
