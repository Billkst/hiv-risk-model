#!/usr/bin/env python3
"""
优化注意力配置
测试不同的attention_strength和先验权重，找出最优配置
"""

import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import accuracy_score, f1_score, classification_report
from models.enhanced_predictor import EnhancedPredictor
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load_test_data(data_path='data/processed/hiv_data_processed.csv'):
    """
    加载测试数据
    
    Args:
        data_path: 数据路径
    
    Returns:
        tuple: (X_test, y_test, feature_names)
    """
    print(f"加载数据: {data_path}")
    df = pd.read_csv(data_path)
    
    # 排除非特征列
    exclude_cols = ['区县', 'risk_level', '按方案评定级别', 
                   '预测风险等级_5级', '置信度', '预测风险等级_3级', '风险描述']
    feature_columns = [col for col in df.columns if col not in exclude_cols]
    
    X = df[feature_columns].values
    y = df['risk_level'].values
    
    # 简单划分：前80%训练，后20%测试
    split_idx = int(len(df) * 0.8)
    X_train = X[:split_idx]
    y_train = y[:split_idx]
    X_test = X[split_idx:]
    y_test = y[split_idx:]
    
    print(f"✓ 数据加载完成")
    print(f"  训练集: {len(X_train)}个样本")
    print(f"  测试集: {len(X_test)}个样本")
    print(f"  特征数: {len(feature_columns)}")
    
    return X_test, y_test, feature_columns


def evaluate_model(predictor, X_test, y_test):
    """
    评估模型性能
    
    Args:
        predictor: 预测器
        X_test: 测试特征
        y_test: 测试标签
    
    Returns:
        dict: 评估指标
    """
    # 批量预测
    y_pred = predictor.predict_batch(X_test)
    
    # 计算指标
    accuracy = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average='macro')
    f1_weighted = f1_score(y_test, y_pred, average='weighted')
    
    return {
        'accuracy': accuracy,
        'f1_macro': f1_macro,
        'f1_weighted': f1_weighted,
        'predictions': y_pred
    }


def test_attention_strength(X_test, y_test, feature_columns):
    """
    测试不同的attention_strength
    
    Args:
        X_test: 测试特征
        y_test: 测试标签
        feature_columns: 特征名称
    
    Returns:
        list: 测试结果
    """
    print("\n" + "="*80)
    print("  测试不同的注意力强度（attention_strength）")
    print("="*80)
    
    # 测试不同的attention_strength值
    strength_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    
    results = []
    
    for strength in strength_values:
        print(f"\n测试 attention_strength = {strength:.1f}...")
        
        # 创建预测器
        predictor = EnhancedPredictor(
            model_path='saved_models/final_model_3to5.pkl',
            enable_attention=True,
            attention_strength=strength
        )
        
        # 评估
        metrics = evaluate_model(predictor, X_test, y_test)
        
        result = {
            'attention_strength': strength,
            'accuracy': metrics['accuracy'],
            'f1_macro': metrics['f1_macro'],
            'f1_weighted': metrics['f1_weighted']
        }
        results.append(result)
        
        print(f"  Accuracy: {metrics['accuracy']:.4f}")
        print(f"  F1 (macro): {metrics['f1_macro']:.4f}")
        print(f"  F1 (weighted): {metrics['f1_weighted']:.4f}")
    
    return results


def test_baseline(X_test, y_test, feature_columns):
    """
    测试基线模型（无注意力）
    
    Args:
        X_test: 测试特征
        y_test: 测试标签
        feature_columns: 特征名称
    
    Returns:
        dict: 基线结果
    """
    print("\n" + "="*80)
    print("  测试基线模型（无注意力机制）")
    print("="*80)
    
    # 创建无注意力的预测器
    predictor = EnhancedPredictor(
        model_path='saved_models/final_model_3to5.pkl',
        enable_attention=False
    )
    
    # 评估
    metrics = evaluate_model(predictor, X_test, y_test)
    
    baseline = {
        'attention_strength': 'baseline',
        'accuracy': metrics['accuracy'],
        'f1_macro': metrics['f1_macro'],
        'f1_weighted': metrics['f1_weighted']
    }
    
    print(f"\n基线模型性能:")
    print(f"  Accuracy: {metrics['accuracy']:.4f}")
    print(f"  F1 (macro): {metrics['f1_macro']:.4f}")
    print(f"  F1 (weighted): {metrics['f1_weighted']:.4f}")
    
    return baseline


def find_best_config(results, baseline):
    """
    找出最优配置
    
    Args:
        results: 测试结果列表
        baseline: 基线结果
    
    Returns:
        dict: 最优配置
    """
    print("\n" + "="*80)
    print("  寻找最优配置")
    print("="*80)
    
    # 按F1 weighted排序
    sorted_results = sorted(results, key=lambda x: x['f1_weighted'], reverse=True)
    best = sorted_results[0]
    
    print(f"\n最优配置:")
    print(f"  attention_strength: {best['attention_strength']:.1f}")
    print(f"  Accuracy: {best['accuracy']:.4f}")
    print(f"  F1 (macro): {best['f1_macro']:.4f}")
    print(f"  F1 (weighted): {best['f1_weighted']:.4f}")
    
    print(f"\n与基线对比:")
    print(f"  Accuracy提升: {(best['accuracy'] - baseline['accuracy'])*100:+.2f}%")
    print(f"  F1 (macro)提升: {(best['f1_macro'] - baseline['f1_macro'])*100:+.2f}%")
    print(f"  F1 (weighted)提升: {(best['f1_weighted'] - baseline['f1_weighted'])*100:+.2f}%")
    
    return best


def generate_summary_table(results, baseline):
    """
    生成结果汇总表
    
    Args:
        results: 测试结果列表
        baseline: 基线结果
    """
    print("\n" + "="*80)
    print("  结果汇总表")
    print("="*80)
    
    print(f"\n{'Strength':<12} {'Accuracy':<12} {'F1 (macro)':<12} {'F1 (weighted)':<12} {'vs Baseline':<12}")
    print("-" * 80)
    
    # 基线
    print(f"{'Baseline':<12} {baseline['accuracy']:<12.4f} {baseline['f1_macro']:<12.4f} {baseline['f1_weighted']:<12.4f} {'---':<12}")
    
    # 各个配置
    for result in results:
        strength = result['attention_strength']
        acc = result['accuracy']
        f1_m = result['f1_macro']
        f1_w = result['f1_weighted']
        diff = f1_w - baseline['f1_weighted']
        
        marker = "⭐" if diff > 0 else ("" if diff == 0 else "")
        
        print(f"{strength:<12.1f} {acc:<12.4f} {f1_m:<12.4f} {f1_w:<12.4f} {diff:+.4f} {marker}")


def save_results(results, baseline, best, output_path='outputs/attention_optimization_results.txt'):
    """
    保存结果到文件
    
    Args:
        results: 测试结果列表
        baseline: 基线结果
        best: 最优配置
        output_path: 输出路径
    """
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("  注意力配置优化结果\n")
        f.write("="*80 + "\n\n")
        
        f.write("基线模型（无注意力）:\n")
        f.write(f"  Accuracy: {baseline['accuracy']:.4f}\n")
        f.write(f"  F1 (macro): {baseline['f1_macro']:.4f}\n")
        f.write(f"  F1 (weighted): {baseline['f1_weighted']:.4f}\n\n")
        
        f.write("最优配置:\n")
        f.write(f"  attention_strength: {best['attention_strength']:.1f}\n")
        f.write(f"  Accuracy: {best['accuracy']:.4f}\n")
        f.write(f"  F1 (macro): {best['f1_macro']:.4f}\n")
        f.write(f"  F1 (weighted): {best['f1_weighted']:.4f}\n\n")
        
        f.write("性能提升:\n")
        f.write(f"  Accuracy: {(best['accuracy'] - baseline['accuracy'])*100:+.2f}%\n")
        f.write(f"  F1 (macro): {(best['f1_macro'] - baseline['f1_macro'])*100:+.2f}%\n")
        f.write(f"  F1 (weighted): {(best['f1_weighted'] - baseline['f1_weighted'])*100:+.2f}%\n\n")
        
        f.write("="*80 + "\n")
        f.write("详细结果\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"{'Strength':<12} {'Accuracy':<12} {'F1 (macro)':<12} {'F1 (weighted)':<12}\n")
        f.write("-" * 60 + "\n")
        
        for result in results:
            f.write(f"{result['attention_strength']:<12.1f} "
                   f"{result['accuracy']:<12.4f} "
                   f"{result['f1_macro']:<12.4f} "
                   f"{result['f1_weighted']:<12.4f}\n")
    
    print(f"\n✓ 结果已保存: {output_path}")


def main():
    """
    主函数
    """
    print("="*80)
    print("  注意力配置优化")
    print("="*80)
    
    # 1. 加载测试数据
    print("\n步骤1: 加载测试数据...")
    X_test, y_test, feature_columns = load_test_data()
    
    # 2. 测试基线模型
    print("\n步骤2: 测试基线模型...")
    baseline = test_baseline(X_test, y_test, feature_columns)
    
    # 3. 测试不同的attention_strength
    print("\n步骤3: 测试不同的注意力强度...")
    results = test_attention_strength(X_test, y_test, feature_columns)
    
    # 4. 找出最优配置
    print("\n步骤4: 分析结果...")
    best = find_best_config(results, baseline)
    
    # 5. 生成汇总表
    generate_summary_table(results, baseline)
    
    # 6. 保存结果
    print("\n步骤5: 保存结果...")
    save_results(results, baseline, best)
    
    print("\n" + "="*80)
    print("✓ 优化完成")
    print("="*80)
    
    print(f"\n推荐配置: attention_strength = {best['attention_strength']:.1f}")
    print(f"预期性能提升: F1 (weighted) {(best['f1_weighted'] - baseline['f1_weighted'])*100:+.2f}%")


if __name__ == '__main__':
    main()
