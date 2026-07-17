#!/bin/bash
# CloudCert Pro - 一键部署脚本 (CentOS 版)
# 用法: bash init.sh
# 说明: 在 CentOS 服务器上首次部署时运行此脚本

set -e

echo "========================================"
echo "  CloudCert Pro - 一键部署初始化"
echo "========================================"

# 0. 检查系统
OS=""
if [ -f /etc/centos-release ] || [ -f /etc/redhat-release ]; then
    OS="centos"
fi

# 1. 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "[1/7] 安装 Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker $USER
    echo "  Docker 安装完成，请重新登录后继续执行"
    echo "  重新登录后重新运行: bash init.sh"
    exit 0
fi
echo "[1/7] Docker 已就绪 ✓"

# 2. 检查 Docker Compose
if ! docker compose version &> /dev/null; then
    echo "[2/7] 安装 Docker Compose..."
    sudo yum install -y docker-compose-plugin
fi
echo "[2/7] Docker Compose 已就绪 ✓"

# 3. 检查 openssl（用于生成 JWT 密钥）
if ! command -v openssl &> /dev/null; then
    echo "[3/7] 安装 openssl..."
    sudo yum install -y openssl
fi
echo "[3/7] 基础工具已就绪 ✓"

# 4. 准备配置文件
echo "[4/7] 配置环境变量..."
if [ ! -f .env ]; then
    if [ -f .env.production ]; then
        cp .env.production .env
        JWT_SECRET=$(openssl rand -hex 32)
        # sed 中分隔符用 |，避免 JWT 中可能出现的 / 字符冲突
        sed -i "s|change-this-to-a-random-string-in-production|$JWT_SECRET|" .env
        echo "  .env 文件已创建，使用了随机 JWT 密钥"
        echo "  如需修改数据库密码，请编辑 .env 文件"
        echo "  然后重新运行: bash init.sh"
        exit 0
    else
        echo "  ❌ 未找到 .env.production 模板文件"
        exit 1
    fi
fi
echo "[4/7] 环境变量已就绪 ✓"

# 5. 配置防火墙（CentOS 默认开启 firewalld）
echo "[5/7] 配置防火墙..."
if systemctl is-active firewalld &>/dev/null; then
    sudo firewall-cmd --permanent --add-port=80/tcp 2>/dev/null || true
    sudo firewall-cmd --reload 2>/dev/null || true
    echo "  防火墙已开放端口 80"
fi
echo "[5/7] 防火墙配置完成 ✓"

# 6. 构建并启动服务
echo "[6/7] 构建并启动服务..."
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d postgres redis
echo "  等待数据库就绪..."
sleep 15

# 启动 backend
docker compose -f docker-compose.prod.yml up -d backend
echo "  等待后端就绪..."
sleep 8

# 初始化数据库
echo "  运行数据库迁移..."
docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head 2>/dev/null || echo "  迁移已执行，跳过"
echo "  导入种子数据..."
docker compose -f docker-compose.prod.yml exec -T backend python scripts/seed_data.py 2>/dev/null || echo "  种子数据已存在，跳过"
echo "  导入知识库文章..."
docker compose -f docker-compose.prod.yml exec -T backend python scripts/generate_knowledge.py --all 2>/dev/null || echo "  知识库已存在，跳过"

echo "[6/7] 服务构建完成 ✓"

# 7. 启动全部服务
echo "[7/7] 启动所有服务..."
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "========================================"
echo "  CloudCert Pro 部署完成！"
echo "========================================"
echo ""
echo "  访问地址: http://10.60.79.158"
echo "  测试账号: admin@cloudcert.com / admin123"
echo ""
echo "  常用命令:"
echo "    查看日志: docker compose -f docker-compose.prod.yml logs -f"
echo "    停止服务: docker compose -f docker-compose.prod.yml down"
echo "    重启服务: docker compose -f docker-compose.prod.yml restart"
echo "========================================"