from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：初始化数据库表
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"[INFO] 数据库表创建跳过: {e}")
    yield
    # 关闭时
    engine.dispose()


app = FastAPI(
    title="CloudCert Pro API",
    description="云认证考试平台后端 API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
