#!/bin/bash
# CloudCert Pro - 停止服务脚本

docker compose -f docker-compose.prod.yml down
echo "所有服务已停止"
