# ☁️ CloudCert Pro

云认证考试平台 — 帮助您高效备考 AWS、Azure、GCP 等云认证。

## 技术栈

- **后端**: Python FastAPI + SQLAlchemy (Async) + PostgreSQL
- **前端**: React 19 + TypeScript + Tailwind CSS v4 + Zustand
- **基础设施**: Docker Compose (PostgreSQL, Redis, MinIO)
- **异步任务**: Celery + Redis
- **认证**: JWT (Access Token + Refresh Token)

## 快速启动

### 1. 启动基础设施

```bash
docker-compose up -d postgres redis minio
docker-compose exec postgres createdb -U postgres cloudcert
```

### 2. 后端启动

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 3. 导入种子数据

```bash
python scripts/seed_data.py
```

### 4. 前端启动

```bash
cd frontend
npm install
npm run dev
```

## 访问地址

- **前端**: http://localhost:5173
- **API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **MinIO控制台**: http://localhost:9001

## 测试账号

- **管理员**: admin@cloudcert.com / admin123

## 项目结构

详见 `CloudCertPro_Implementation.md`

## API 路由

| 模块 | 路径 | 说明 |
|------|------|------|
| 认证 | `/api/v1/auth/*` | 注册、登录、Token刷新 |
| 认证列表 | `/api/v1/certifications` | 云认证与科目 |
| 题库 | `/api/v1/questions` | 题目列表与详情 |
| 考试 | `/api/v1/exams` | 创建考试、交卷、结果 |
| 报告 | `/api/v1/reports/:id` | 评估报告 |
| 错题本 | `/api/v1/wrong-book` | 错题管理 |
| 知识库 | `/api/v1/knowledge` | 知识文章 |
