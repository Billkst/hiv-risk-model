"""
检查模型参数量
"""
import joblib
import numpy as np
import os

# 加载模型
model_info = joblib.load('saved_models/final_model_3to5.pkl')
model = model_info['model']

print('=' * 80)
print('模型参数统计')
print('=' * 80)

# 模型类型
print(f'\n模型类型: {model_info["model_name"]}')
print(f'特征数量: {len(model_info["feature_columns"])}')

# Gradient Boosting 模型参数
if hasattr(model, 'n_estimators'):
    print(f'\n决策树数量 (n_estimators): {model.n_estimators}')
    
if hasattr(model, 'max_depth'):
    print(f'最大深度 (max_depth): {model.max_depth}')
    
if hasattr(model, 'learning_rate'):
    print(f'学习率 (learning_rate): {model.learning_rate}')

if hasattr(model, 'min_samples_split'):
    print(f'最小分裂样本数 (min_samples_split): {model.min_samples_split}')

if hasattr(model, 'min_samples_leaf'):
    print(f'最小叶子样本数 (min_samples_leaf): {model.min_samples_leaf}')

# 计算总参数量
# 对于 Gradient Boosting，参数量 = 树的数量 × 每棵树的节点数
if hasattr(model, 'estimators_'):
    total_nodes = 0
    total_leaves = 0
    max_nodes_per_tree = 0
    min_nodes_per_tree = float('inf')
    
    for estimator_array in model.estimators_:
        for tree in estimator_array:
            # 每个节点有：特征索引、阈值、左子节点、右子节点、值
            n_nodes = tree.tree_.node_count
            n_leaves = tree.tree_.n_leaves
            total_nodes += n_nodes
            total_leaves += n_leaves
            max_nodes_per_tree = max(max_nodes_per_tree, n_nodes)
            min_nodes_per_tree = min(min_nodes_per_tree, n_nodes)
    
    n_trees = len(model.estimators_) * len(model.estimators_[0])
    avg_nodes_per_tree = total_nodes / n_trees
    
    print(f'\n树的统计:')
    print(f'  总树数: {n_trees}')
    print(f'  总节点数: {total_nodes:,}')
    print(f'  总叶子节点数: {total_leaves:,}')
    print(f'  平均每棵树节点数: {avg_nodes_per_tree:.1f}')
    print(f'  最大节点数/树: {max_nodes_per_tree}')
    print(f'  最小节点数/树: {min_nodes_per_tree}')
    
    # 每个节点大约有 5 个参数（特征索引、阈值、左右子节点索引、预测值）
    total_params = total_nodes * 5
    print(f'\n参数量估计:')
    print(f'  总参数量: {total_params:,}')
    print(f'  参数量 (K): {total_params / 1000:.1f}K')
    print(f'  参数量 (M): {total_params / 1000000:.2f}M')

# 模型文件大小
model_size = os.path.getsize('saved_models/final_model_3to5.pkl')
print(f'\n模型文件大小:')
print(f'  大小 (KB): {model_size / 1024:.2f} KB')
print(f'  大小 (MB): {model_size / (1024*1024):.2f} MB')

# 输出类别数
if hasattr(model, 'n_classes_'):
    print(f'\n输出类别数: {model.n_classes_}')

print('\n' + '=' * 80)
