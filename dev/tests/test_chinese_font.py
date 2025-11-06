"""
测试中文字体显示
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path
import numpy as np

# 加载中文字体
user_font_path = Path.home() / '.fonts' / 'SourceHanSansSC.otf'
if user_font_path.exists():
    fm.fontManager.addfont(str(user_font_path))
    plt.rcParams['font.sans-serif'] = ['Source Han Sans SC', 'DejaVu Sans']
    print(f"✓ 使用字体: Source Han Sans SC")
else:
    print(f"✗ 字体文件不存在: {user_font_path}")

plt.rcParams['axes.unicode_minus'] = False

# 创建测试图表
fig, ax = plt.subplots(figsize=(10, 6))

# 测试数据
features = ['存活数', '新报告', '感染率', '治疗覆盖率', '病毒抑制比例']
values = [0.38, 0.29, 0.18, -0.22, -0.15]
colors = ['#d62728' if v > 0 else '#1f77b4' for v in values]

# 绘制条形图
y_pos = np.arange(len(features))
ax.barh(y_pos, values, color=colors, alpha=0.7)

# 设置标签
ax.set_yticks(y_pos)
ax.set_yticklabels(features, fontsize=12)
ax.set_xlabel('特征贡献度', fontsize=12)
ax.set_title('中文字体测试 - 特征贡献度示例', fontsize=14, fontweight='bold')

# 添加网格
ax.grid(axis='x', alpha=0.3, linestyle='--')
ax.axvline(x=0, color='black', linewidth=0.8)

# 添加数值标签
for i, v in enumerate(values):
    x_pos = v + (0.01 if v > 0 else -0.01)
    ha = 'left' if v > 0 else 'right'
    ax.text(x_pos, i, f'{v:+.2f}', va='center', ha=ha, fontsize=10)

# 添加图例
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='#d62728', alpha=0.7, label='正贡献（增加风险）'),
    Patch(facecolor='#1f77b4', alpha=0.7, label='负贡献（降低风险）')
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=10)

plt.tight_layout()

# 保存
output_path = 'outputs/visualizations/chinese_font_test.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"✓ 测试图表已保存: {output_path}")

plt.close()

print("\n请打开图表查看中文是否正确显示:")
print(f"  {output_path}")
print("\n如果中文显示正常，说明字体配置成功！")
