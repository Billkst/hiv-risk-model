#!/bin/bash
# 快速修复和重新测试脚本

echo "=========================================="
echo "HIV模型增强功能 - 问题修复"
echo "=========================================="

# 1. 安装中文字体
echo -e "\n[1/4] 检查中文字体..."
if fc-list :lang=zh | grep -q "WenQuanYi"; then
    echo "✓ 中文字体已安装"
else
    echo "⚠️  中文字体未安装，尝试安装..."
    sudo apt-get update > /dev/null 2>&1
    sudo apt-get install -y fonts-wqy-microhei fonts-wqy-zenhei > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ 中文字体安装成功"
    else
        echo "✗ 中文字体安装失败（可能需要sudo权限）"
    fi
fi

# 2. 清除matplotlib缓存
echo -e "\n[2/4] 清除matplotlib缓存..."
rm -rf ~/.cache/matplotlib
echo "✓ 缓存已清除"

# 3. 重新生成可视化
echo -e "\n[3/4] 重新生成可视化图表..."
cd "$(dirname "$0")"
python3 visualize_contributions.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ 可视化图表生成成功"
    echo "  生成的图表:"
    ls -lh outputs/visualizations/*.png 2>/dev/null | awk '{print "  - "$9" ("$5")"}'
else
    echo "✗ 可视化图表生成失败"
fi

# 4. 提示重启API
echo -e "\n[4/4] API服务提示..."
if pgrep -f "api/app.py" > /dev/null; then
    echo "⚠️  检测到API服务正在运行"
    echo "  请按以下步骤重启API服务:"
    echo "  1. 在运行API的终端按 Ctrl+C 停止服务"
    echo "  2. 重新运行: python3 api/app.py"
    echo "  3. 确认看到: ✓ 特征贡献度分析器已启用"
else
    echo "ℹ️  API服务未运行"
    echo "  启动命令: python3 api/app.py"
fi

echo -e "\n=========================================="
echo "修复完成！"
echo "=========================================="
echo -e "\n下一步:"
echo "1. 查看可视化图表: outputs/visualizations/"
echo "2. 重启API服务（如果正在运行）"
echo "3. 重新运行测试: python3 test_api_enhanced.py"
