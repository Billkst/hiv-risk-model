"""
模型评估模块
提供各种评估指标和可视化
"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score
)
from sklearn.preprocessing import label_binarize


class ModelEvaluator:
    """模型评估类"""
    
    def __init__(self, model_name="Model"):
        self.model_name = model_name
        
    def evaluate(self, y_true, y_pred, y_pred_proba=None):
        """完整的模型评估"""
        print("\n" + "=" * 60)
        print(f"{self.model_name} - 评估结果")
        print("=" * 60)
        
        # 1. 基本指标
        accuracy = accuracy_score(y_true, y_pred)
        print(f"\n准确率 (Accuracy): {accuracy:.4f}")
        
        # 2. 各类别指标（使用 weighted 平均）
        precision = precision_score(y_true, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_true, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        
        print(f"精确率 (Precision): {precision:.4f}")
        print(f"召回率 (Recall): {recall:.4f}")
        print(f"F1分数 (F1-Score): {f1:.4f}")
        
        # 3. 详细分类报告
        print(f"\n详细分类报告:")
        print("-" * 60)
        report = classification_report(y_true, y_pred, zero_division=0)
        print(report)
        
        # 4. 混淆矩阵
        print(f"混淆矩阵:")
        print("-" * 60)
        cm = confusion_matrix(y_true, y_pred)
        self._print_confusion_matrix(cm, y_true)
        
        # 5. ROC-AUC（如果有概率预测）
        if y_pred_proba is not None:
            try:
                # 获取所有类别
                classes = np.unique(y_true)
                n_classes = len(classes)
                
                if n_classes > 2:
                    # 多分类：使用 one-vs-rest
                    y_true_bin = label_binarize(y_true, classes=classes)
                    
                    # 确保 y_pred_proba 包含所有类别的概率
                    if y_pred_proba.shape[1] == n_classes:
                        auc = roc_auc_score(y_true_bin, y_pred_proba, average='weighted', multi_class='ovr')
                        print(f"\nROC-AUC (weighted): {auc:.4f}")
                    else:
                        print(f"\n⚠️  无法计算 ROC-AUC：预测概率维度不匹配")
                else:
                    # 二分类
                    auc = roc_auc_score(y_true, y_pred_proba[:, 1])
                    print(f"\nROC-AUC: {auc:.4f}")
            except Exception as e:
                print(f"\n⚠️  ROC-AUC 计算失败: {e}")
        
        # 返回评估指标字典
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'confusion_matrix': cm
        }
        
        return metrics
    
    def _print_confusion_matrix(self, cm, y_true):
        """打印格式化的混淆矩阵"""
        classes = sorted(np.unique(y_true))
        
        # 打印表头
        header = "实际\\预测"
        print(f"{header:<12}", end="")
        for cls in classes:
            print(f"等级{cls:<8}", end="")
        print()
        print("-" * (12 + 10 * len(classes)))
        
        # 打印每一行
        for i, cls in enumerate(classes):
            print(f"等级{cls:<8}", end="")
            for j in range(len(classes)):
                if i < len(cm) and j < len(cm[i]):
                    print(f"{cm[i][j]:<10}", end="")
                else:
                    print(f"{'0':<10}", end="")
            print()
    
    def compare_models(self, results_dict):
        """比较多个模型的性能"""
        print("\n" + "=" * 80)
        print("模型性能对比")
        print("=" * 80)
        
        # 创建对比表格
        comparison_data = []
        for model_name, metrics in results_dict.items():
            comparison_data.append({
                '模型': model_name,
                '准确率': f"{metrics['accuracy']:.4f}",
                '精确率': f"{metrics['precision']:.4f}",
                '召回率': f"{metrics['recall']:.4f}",
                'F1分数': f"{metrics['f1_score']:.4f}"
            })
        
        df_comparison = pd.DataFrame(comparison_data)
        print(df_comparison.to_string(index=False))
        
        # 找出最佳模型
        best_model = max(results_dict.items(), key=lambda x: x[1]['f1_score'])
        print(f"\n🏆 最佳模型: {best_model[0]} (F1={best_model[1]['f1_score']:.4f})")
        
        return df_comparison
    
    def evaluate_per_class(self, y_true, y_pred):
        """每个类别的详细评估"""
        print("\n" + "=" * 60)
        print("各类别详细评估")
        print("=" * 60)
        
        classes = sorted(np.unique(y_true))
        
        for cls in classes:
            # 该类别的样本数
            n_samples = (y_true == cls).sum()
            
            # 该类别的预测正确数
            correct = ((y_true == cls) & (y_pred == cls)).sum()
            
            # 该类别的准确率
            if n_samples > 0:
                class_acc = correct / n_samples
                print(f"\n等级 {cls}:")
                print(f"  样本数: {n_samples}")
                print(f"  预测正确: {correct}")
                print(f"  准确率: {class_acc:.4f}")
            else:
                print(f"\n等级 {cls}: 无样本")


if __name__ == '__main__':
    # 测试评估器
    from sklearn.datasets import make_classification
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    
    # 生成测试数据
    X, y = make_classification(n_samples=200, n_features=20, n_informative=15,
                               n_classes=5, n_clusters_per_class=1, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    
    # 训练模型
    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, y_train)
    
    # 预测
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)
    
    # 评估
    evaluator = ModelEvaluator("Random Forest")
    metrics = evaluator.evaluate(y_test, y_pred, y_pred_proba)
    evaluator.evaluate_per_class(y_test, y_pred)
