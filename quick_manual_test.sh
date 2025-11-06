#!/bin/bash
# HIV风险评估模型 - 快速手动测试脚本
# 使用方法: bash quick_manual_test.sh

# 不使用 set -e，让所有测试都能运行

echo "=========================================="
echo "HIV风险评估模型 - 快速测试"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数器
PASSED=0
FAILED=0

# 测试函数
test_item() {
    local test_name=$1
    local test_command=$2
    
    echo -n "测试: $test_name ... "
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 通过${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ 失败${NC}"
        ((FAILED++))
        return 1
    fi
}

echo "1️⃣  目录结构测试"
echo "-------------------"
test_item "core目录存在" "[ -d core ]"
test_item "docs目录存在" "[ -d docs ]"
test_item "dev目录存在" "[ -d dev ]"
test_item "data目录存在" "[ -d data ]"
echo ""

echo "2️⃣  符号链接测试"
echo "-------------------"
test_item "README.md符号链接" "[ -L README.md ] && [ -e README.md ]"
test_item "models目录符号链接" "[ -L models ] && [ -d models ]"
test_item "api目录符号链接" "[ -L api ] && [ -d api ]"
test_item "predictor.py可访问" "[ -f models/predictor.py ]"
echo ""

echo "3️⃣  Python导入测试"
echo "-------------------"
test_item "导入HIVRiskPredictor" "python -c 'import sys; sys.path.insert(0, \".\"); from models.predictor import HIVRiskPredictor'"
test_item "导入enhanced_predictor" "python -c 'import sys; sys.path.insert(0, \".\"); import models.enhanced_predictor'"
test_item "导入API app" "python -c 'import sys; sys.path.insert(0, \".\"); from api.app import app'"
echo ""

echo "4️⃣  文件完整性测试"
echo "-------------------"
test_item "requirements.txt存在" "[ -f requirements.txt ]"
test_item "Dockerfile存在" "[ -f Dockerfile ]"
test_item "core/api/app.py存在" "[ -f core/api/app.py ]"
test_item "core/models/predictor.py存在" "[ -f core/models/predictor.py ]"
echo ""

echo "5️⃣  文档测试"
echo "-------------------"
test_item "用户README存在" "[ -f docs/user/README.md ]"
test_item "API文档存在" "[ -f docs/user/API_DOCUMENTATION.md ]"
test_item "部署指南存在" "[ -f docs/deployment/DEPLOYMENT_GUIDE.md ]"
test_item "测试指南存在" "[ -f MANUAL_TESTING_GUIDE.md ]"
echo ""

echo "=========================================="
echo "测试总结"
echo "=========================================="
echo -e "通过: ${GREEN}$PASSED${NC}"
echo -e "失败: ${RED}$FAILED${NC}"
echo "总计: $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  有 $FAILED 个测试失败，请查看详细测试指南${NC}"
    echo "详细测试: cat MANUAL_TESTING_GUIDE.md"
    exit 1
fi
