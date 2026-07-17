#!/bin/bash
# 数据库初始化脚本

echo "🚀 正在初始化 CloudCert Pro 数据库..."

# 创建数据库
docker-compose exec -T postgres createdb -U postgres cloudcert 2>/dev/null || echo "数据库可能已存在，跳过创建"

# 运行迁移
cd backend
alembic upgrade head

# 导入种子数据
cd ..
python scripts/seed_data.py

echo "✅ 数据库初始化完成！"
echo "  管理员账号: admin@cloudcert.com / admin123"
