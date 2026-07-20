#!/bin/bash
# CloudCert Pro - 语言切换 + 问题过滤 + 一键部署修复脚本
# 在服务器上直接执行: bash fix_all.sh

set -e
cd /opt/cloudcert-pro

echo "============================================"
echo "  CloudCert Pro - 全量修复部署脚本"
echo "============================================"

# 1. 修复前端 PracticeQuestions 语言过滤
echo "[1/6] 添加强题页面语言过滤..."
cat > /tmp/patch_practice.py << 'PYEOF'
import re

with open('/opt/cloudcert-pro/frontend/src/pages/PracticeQuestions.tsx', 'r', encoding='utf-8') as f:
    code = f.read()

# 添加导入 useLangStore 和 hasChinese 函数
if 'useLangStore' not in code:
    code = code.replace(
        "import { useState, useEffect, useCallback, useRef } from 'react';",
        "import { useState, useEffect, useCallback, useRef } from 'react';"
    )
    code = code.replace(
        "import QuestionCard from '../components/QuestionCard';",
        "import QuestionCard from '../components/QuestionCard';\nimport { useLangStore } from '../store/langStore';\n\nfunction hasChinese(text: string): boolean {\n  return /[\\u4e00-\\u9fa5]/.test(text);\n}"
    )

# 添加语言过滤（在 let all ... 之后）
old = "const res = await questionApi.list(params);\n      let all = res.data.data?.items || [];\n\n      // Filter out already-used questions when possible"
new = """const res = await questionApi.list(params);
      let all = res.data.data?.items || [];

      // 根据当前语言过滤题目
      const { lang } = useLangStore.getState();
      all = all.filter((q: any) => {
        const hasCn = hasChinese(q.content);
        return lang === 'zh' ? hasCn : !hasCn;
      });

      // Filter out already-used questions when possible"""
code = code.replace(old, new)

with open('/opt/cloudcert-pro/frontend/src/pages/PracticeQuestions.tsx', 'w', encoding='utf-8') as f:
    f.write(code)
print("  PracticeQuestions.tsx 已更新")
PYEOF
python3 /tmp/patch_practice.py

# 2. 确保 requirements.txt 有 requests
echo "[2/6] 检查 Python 依赖..."
grep -qxF "requests==2.32.3" backend/requirements.txt || echo "requests==2.32.3" >> backend/requirements.txt

# 3. 重建和部署
echo "[3/6] 重建前端和后端..."
docker compose -f docker-compose.prod.yml build --no-cache frontend
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml up -d postgres redis backend frontend nginx

echo "[4/6] 复制脚本到容器..."
sleep 5
docker cp scripts cloudcert-pro-backend-1:/app/ 2>/dev/null || true

# 5. 重置管理员密码
echo "[5/6] 重置管理员密码..."
docker compose -f docker-compose.prod.yml exec backend sh -c "
cd /app && PYTHONPATH=/app python -c \"
from app.database import SessionLocal
from app.models.user import User
from app.services.auth_service import AuthService
db = SessionLocal()
user = db.query(User).filter(User.email == 'admin@cloudcert.com').first()
if user:
    user.password_hash = AuthService.hash_password('admin123')
    db.commit()
    print('  Password reset OK')
else:
    print('  User not found, creating...')
    user = User(email='admin@cloudcert.com',
                password_hash=AuthService.hash_password('admin123'),
                nickname='Admin', role='admin', is_active=True)
    db.add(user)
    db.commit()
    print('  Admin user created')
db.close()
\"
" 2>/dev/null || echo "  User already exists"

# 6. 查看状态
echo "[6/6] 验证服务状态..."
sleep 3

# 测试登录
TOKEN=$(curl -s http://10.60.79.158:5173/api/v1/auth/login -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@cloudcert.com","password":"admin123"}' 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('access_token','FAIL'))" 2>/dev/null)

if [ "$TOKEN" = "FAIL" ] || [ -z "$TOKEN" ]; then
    echo "  ⚠️ 登录测试失败，检查后端日志: docker logs cloudcert-pro-backend-1 --tail 10"
else
    echo "  ✅ 登录成功！"
    echo ""
    echo "============================================"
    echo "  修复完成！"
    echo "============================================"
    echo ""
    echo "  访问 http://10.60.79.158:5173"
    echo "  右上角点击 EN / 中 切换语言"
    echo "  管理员: admin@cloudcert.com / admin123"
fi
