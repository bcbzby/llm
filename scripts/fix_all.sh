#!/bin/bash
# CloudCert Pro - 服务器一键修复脚本
# 在服务器上直接执行: bash fix_all.sh
# 功能:
#   - 刷题页面中英文切换
#   - 模拟考试页面中英文切换
#   - 管理员密码重置
#   - 依赖修复 + 重建部署

set -e
cd /opt/cloudcert-pro

echo "============================================"
echo "  CloudCert Pro 一键修复部署"
echo "============================================"

echo ""

# ============================================================
# 1. 修复 PracticeQuestions.tsx
# ============================================================
echo "[1/4] 修复刷题页面语言过滤..."
python3 << 'PYFIX1'
with open('frontend/src/pages/PracticeQuestions.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

# 添加 useLangStore 导入 + hasChinese 函数
old_import = "import QuestionCard from '../components/QuestionCard';"
new_import = old_import + "\nimport { useLangStore } from '../store/langStore';\n\nfunction hasChinese(t: string): boolean {\n  return /[\\u4e00-\\u9fa5]/.test(t);\n}"
if 'useLangStore' not in c:
    c = c.replace(old_import, new_import)

# 添加语言过滤
old_filter = "const res = await questionApi.list(params);\n      let all = res.data.data?.items || [];\n\n      // Filter out already-used questions when possible"
new_filter = """const res = await questionApi.list(params);
      let all = res.data.data?.items || [];

      const { lang } = useLangStore.getState();
      all = all.filter((q: any) => {
        return lang === 'zh' ? hasChinese(q.content) : !hasChinese(q.content);
      });

      // Filter out already-used questions when possible"""
if old_filter in c:
    c = c.replace(old_filter, new_filter)
    print("  PracticeQuestions: OK")
else:
    print("  PracticeQuestions: 已修复, 跳过")

with open('frontend/src/pages/PracticeQuestions.tsx', 'w', encoding='utf-8') as f:
    f.write(c)
PYFIX1

# ============================================================
# 2. 修复 ExamTaking.tsx
# ============================================================
echo "[2/4] 修复模拟考试页面语言过滤..."
python3 << 'PYFIX2'
with open('frontend/src/pages/ExamTaking.tsx', 'r', encoding='utf-8') as f:
    c = f.read()

needs_update = False

# 添加导入
old_imp = "import QuestionCard from '../components/QuestionCard';"
new_imp = old_imp + "\nimport { useLangStore } from '../store/langStore';\n\nfunction hasChinese(t: string): boolean {\n  return /[\\u4e00-\\u9fa5]/.test(t);\n}"
if 'useLangStore' not in c:
    c = c.replace(old_imp, new_imp)
    needs_update = True

# 添加语言过滤逻辑 (在 currentQuestion 定义之前)
old_def = "  const currentQuestion = examData?.questions?.[currentIndex] || null;"
new_def = """  const { lang } = useLangStore();

  // 根据语言过滤题目
  const displayQuestions = (examData?.questions || []).filter(q => {
    return lang === 'zh' ? hasChinese(q.content) : !hasChinese(q.content);
  });
  const currentQuestion = displayQuestions.length > 0
    ? (displayQuestions[currentIndex] || null)
    : (examData?.questions?.[currentIndex] || null);"""
if old_def in c:
    c = c.replace(old_def, new_def)
    needs_update = True

# 替换 examData.questions 引用 -> displayQuestions
replacements = [
    ("!examData || !examData.questions || examData.questions.length === 0", "!examData || !displayQuestions || displayQuestions.length === 0"),
    ("examData.questions.filter((q) => !answers.has(q.id))", "displayQuestions.filter((q) => !answers.has(q.id))"),
    ("examData.questions.map((q) => ({", "displayQuestions.map((q) => ({"),
    ("Math.min(examData.questions.length - 1, i + 1)", "Math.min(displayQuestions.length - 1, i + 1)"),
    ("currentIndex === examData.questions.length - 1", "currentIndex === displayQuestions.length - 1"),
    ("examData.questions.map((q, idx)", "displayQuestions.map((q, idx)"),
]

for old_txt, new_txt in replacements:
    if old_txt in c:
        c = c.replace(old_txt, new_txt)
        needs_update = True

if needs_update:
    print("  ExamTaking: OK")
else:
    print("  ExamTaking: 已修复, 跳过")

with open('frontend/src/pages/ExamTaking.tsx', 'w', encoding='utf-8') as f:
    f.write(c)
PYFIX2

# ============================================================
# 3. 修复依赖 + 管理员密码
# ============================================================
echo "[3/4] 修复依赖和密码..."
grep -qxF "requests==2.32.3" backend/requirements.txt || echo "requests==2.32.3" >> backend/requirements.txt
echo "  requirements: OK"

# 重置管理员密码
docker compose -f docker-compose.prod.yml exec backend sh -c "
cd /app && PYTHONPATH=/app python -c '
from app.database import SessionLocal
from app.models.user import User
from app.services.auth_service import AuthService
db = SessionLocal()
u = db.query(User).filter(User.email == \"admin@cloudcert.com\").first()
if u:
    u.password_hash = AuthService.hash_password(\"admin123\")
    db.commit()
    print(\"  密码: OK\")
else:
    print(\"  账号不存在, 创建中...\")
    u = User(email=\"admin@cloudcert.com\",
        password_hash=AuthService.hash_password(\"admin123\"),
        nickname=\"Admin\", role=\"admin\", is_active=True)
    db.add(u)
    db.commit()
    print(\"  账号: 已创建\")
db.close()
'
" 2>/dev/null || echo "  密码重置跳过"

# ============================================================
# 4. 重建部署
# ============================================================
echo "[4/4] 重建部署..."
echo "  构建前端(无缓存)..."
docker compose -f docker-compose.prod.yml build --no-cache frontend 2>&1 | tail -3
echo "  重启服务..."
docker compose -f docker-compose.prod.yml up -d frontend nginx 2>/dev/null || true

sleep 3
echo ""

# ============================================================
# 验证
# ============================================================
echo "============================================"
echo "  验证服务..."
TOKEN=$(curl -s http://10.60.79.158:5173/api/v1/auth/login -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@cloudcert.com","password":"admin123"}' 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('access_token','') or 'FAIL')")

if [ "$TOKEN" = "FAIL" ] || [ -z "$TOKEN" ]; then
    echo "  ⚠️ 登录失败, 检查: docker logs cloudcert-pro-backend-1 --tail 5"
else
    echo "  ✅ 登录成功!"
fi
echo "============================================"
echo ""
echo "  访问: http://10.60.79.158:5173"
echo "  账号: admin@cloudcert.com / admin123"
echo "  右上角 EN / 中 切换语言"
echo "============================================"
