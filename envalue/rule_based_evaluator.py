"""
基于规则匹配的评估系统
用于评估JSON数据提取结果，不依赖大模型，提供固定的评估基准
"""

import pandas as pd
import json
import re
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path


class RuleBasedEvaluator:
    """基于规则的评估器"""
    
    def __init__(self, ground_truth_csv: str):
        """
        初始化评估器
        
        Args:
            ground_truth_csv: 基准集CSV文件路径
        """
        self.ground_truth_df = self._load_and_clean_ground_truth(ground_truth_csv)
        self.ground_truth_dict = self._build_ground_truth_dict()
    
    def _load_and_clean_ground_truth(self, csv_path: str) -> pd.DataFrame:
        """
        加载并清理基准集数据，去除空值行
        
        Args:
            csv_path: CSV文件路径
            
        Returns:
            清理后的DataFrame
        """
        df = pd.read_csv(csv_path)
        
        # 去除 Ground Truth 列为空的行
        df = df[df['Ground Truth'].notna() & (df['Ground Truth'] != '')]
        
        # 同时也去除 Key 列为空的行
        df = df[df['Key'].notna() & (df['Key'] != '')]
        
        print(f"基准集加载完成: 总共 {len(df)} 条有效记录")
        return df
    
    def _build_ground_truth_dict(self) -> Dict[str, Dict[str, str]]:
        """
        将基准集转换为字典格式，便于快速查找
        
        Returns:
            {File: {Key: Ground_Truth_Value}}
        """
        truth_dict = {}
        for _, row in self.ground_truth_df.iterrows():
            file_name = row['File']
            key = row['Key']
            value = str(row['Ground Truth']) if pd.notna(row['Ground Truth']) else ''
            
            if file_name not in truth_dict:
                truth_dict[file_name] = {}
            truth_dict[file_name][key] = value
        
        return truth_dict
    
    def flatten_json(self, data: Any, parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """
        扁平化JSON数据
        
        Args:
            data: 待扁平化的数据
            parent_key: 父级键名
            sep: 分隔符
            
        Returns:
            扁平化后的字典
        """
        items = []
        
        if isinstance(data, dict):
            for k, v in data.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, (dict, list)):
                    items.extend(self.flatten_json(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
        elif isinstance(data, list):
            for i, v in enumerate(data):
                new_key = f"{parent_key}.{i}" if parent_key else str(i)
                if isinstance(v, (dict, list)):
                    items.extend(self.flatten_json(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
        else:
            items.append((parent_key, data))
        
        # 过滤掉空值
        filtered_items = [(k, v) for k, v in items if v is not None and v != '']
        
        return dict(filtered_items)
    
    def extract_numbers(self, text: str) -> List[float]:
        """
        从文本中提取所有数字（支持整数和浮点数）
        
        Args:
            text: 输入文本
            
        Returns:
            提取的数字列表
        """
        # 匹配整数和浮点数（包括科学计数法）
        pattern = r'-?\d+\.?\d*(?:[eE][+-]?\d+)?'
        matches = re.findall(pattern, str(text))
        return [float(m) for m in matches if m]
    
    def calculate_weight(self, value: str) -> int:
        """
        计算权重：如果值包含>=4个纯数字，权重为数字个数，否则为1
        
        Args:
            value: 待计算的值
            
        Returns:
            权重值
        """
        numbers = self.extract_numbers(str(value))
        if len(numbers) >= 4:
            return len(numbers)
        return 1
    
    def is_pure_number(self, value: str) -> bool:
        """
        判断是否为纯数字
        
        Args:
            value: 待判断的值
            
        Returns:
            是否为纯数字
        """
        try:
            float(str(value).strip())
            return True
        except ValueError:
            return False
    
    def has_mixed_content(self, value: str) -> bool:
        """
        判断是否包含混合内容（数字+字符串）
        
        Args:
            value: 待判断的值
            
        Returns:
            是否为混合内容
        """
        value_str = str(value)
        has_digit = any(c.isdigit() for c in value_str)
        has_letter = any(c.isalpha() for c in value_str)
        return has_digit and (has_letter or any(c in value_str for c in ['/', ':', '-', ' ', '²', '³', '^']))
    
    def compare_values(self, extracted: str, ground_truth: str) -> Tuple[str, str]:
        """
        对比两个值，返回评估状态和原因
        
        Args:
            extracted: 提取的值
            ground_truth: 基准值
            
        Returns:
            (Status, Reason) 元组
        """
        extracted_str = str(extracted).strip()
        ground_truth_str = str(ground_truth).strip()
        
        # 完全匹配
        if extracted_str == ground_truth_str:
            return 'TP', '值完全匹配'
        
        # 纯数字对比
        if self.is_pure_number(extracted_str) and self.is_pure_number(ground_truth_str):
            try:
                if float(extracted_str) == float(ground_truth_str):
                    return 'TP', '数值相等'
                else:
                    return 'FP', f'数值不匹配: 提取值={extracted_str}, 基准值={ground_truth_str}'
            except ValueError:
                return 'FP', '数值转换失败'
        
        # 混合内容对比（字符串+数字）
        if self.has_mixed_content(extracted_str) or self.has_mixed_content(ground_truth_str):
            extracted_nums = self.extract_numbers(extracted_str)
            ground_truth_nums = self.extract_numbers(ground_truth_str)
            
            if extracted_nums == ground_truth_nums:
                return 'TP', f'数值部分匹配: {extracted_nums}'
            else:
                return 'FP', f'数值部分不匹配: 提取={extracted_nums}, 基准={ground_truth_nums}'
        
        # 纯字符串 - 跳过对比
        return 'SKIP', '纯字符串，跳过对比'
    
    def evaluate_json_file(self, json_file_path: str) -> List[Dict[str, Any]]:
        """
        评估单个JSON文件
        
        Args:
            json_file_path: JSON文件路径
            
        Returns:
            评估结果列表
        """
        # 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data = data ['final_result']
        # 扁平化JSON数据
        flattened_data = self.flatten_json(data)
        
        # 获取文件名
        file_name = Path(json_file_path).name
        
        # 获取该文件的基准数据
        ground_truth_for_file = self.ground_truth_dict.get(file_name, {})
        
        if not ground_truth_for_file:
            print(f"警告: 未找到文件 {file_name} 的基准数据")
            return []
        
        results = []
        evaluated_keys = set()
        
        # 1. 对比基准集中存在的键
        for key, ground_truth_value in ground_truth_for_file.items():
            # 计算权重
            weight = self.calculate_weight(ground_truth_value)
            
            if key in flattened_data:
                extracted_value = flattened_data[key]
                status, reason = self.compare_values(extracted_value, ground_truth_value)
                
                results.append({
                    'Key': key,
                    'Extracted Value': extracted_value,
                    'Ground Truth': ground_truth_value,
                    'Status': status,
                    'Reason': reason,
                    'Weight': weight,
                    'File': file_name
                })
                evaluated_keys.add(key)
            else:
                # 基准集中存在但提取数据中不存在 - FN
                results.append({
                    'Key': key,
                    'Extracted Value': '',
                    'Ground Truth': ground_truth_value,
                    'Status': 'FN',
                    'Reason': '基准集中存在但提取数据中缺失',
                    'Weight': weight,
                    'File': file_name
                })
        
        # 2. 对比提取数据中存在但基准集中不存在的键 - FP
        for key, value in flattened_data.items():
            if key not in evaluated_keys and key not in ground_truth_for_file:
                results.append({
                    'Key': key,
                    'Extracted Value': value,
                    'Ground Truth': '',
                    'Status': 'FP',
                    'Reason': '提取数据中存在但基准集中不存在（可能是结构差异或异常）',
                    'Weight': 1,
                    'File': file_name
                })
        
        return results
    
    def evaluate_directory(self, json_dir: str, output_csv: str = None) -> pd.DataFrame:
        """
        评估整个目录中的JSON文件
        
        Args:
            json_dir: JSON文件目录
            output_csv: 输出CSV文件路径（可选）
            
        Returns:
            评估结果DataFrame
        """
        json_dir_path = Path(json_dir)
        all_results = []
        
        # 获取基准集中涉及的所有文件
        unique_files = self.ground_truth_df['File'].unique()
        
        print(f"开始评估 {len(unique_files)} 个文件...")
        
        for file_name in unique_files:
            json_file_path = json_dir_path / file_name
            
            if not json_file_path.exists():
                print(f"警告: 文件不存在 - {json_file_path}")
                continue
            
            print(f"评估文件: {file_name}")
            results = self.evaluate_json_file(str(json_file_path))
            all_results.extend(results)
        
        # 创建结果DataFrame
        results_df = pd.DataFrame(all_results)
        
        # 保存到CSV
        if output_csv:
            results_df.to_csv(output_csv, index=False, encoding='utf-8')
            print(f"\n评估结果已保存到: {output_csv}")
        
        # 打印统计信息
        self._print_statistics(results_df)
        
        return results_df
    
    def _print_statistics(self, results_df: pd.DataFrame):
        """
        打印评估统计信息
        
        Args:
            results_df: 评估结果DataFrame
        """
        print("\n" + "="*60)
        print("评估统计信息")
        print("="*60)
        
        total = len(results_df)
        print(f"总记录数: {total}")
        
        if total > 0:
            # 按权重统计
            weighted_status = results_df.groupby('Status')['Weight'].sum()
            total_weighted = results_df['Weight'].sum()
            
            print("\n状态分布（未加权）:")
            status_counts = results_df['Status'].value_counts()
            for status, count in status_counts.items():
                percentage = (count / total) * 100
                print(f"  {status}: {count} ({percentage:.2f}%)")
            
            print("\n状态分布（加权后）:")
            for status, weighted_count in weighted_status.items():
                percentage = (weighted_count / total_weighted) * 100
                print(f"  {status}: {weighted_count:.0f} ({percentage:.2f}%)")
            
            # 计算准确率（使用加权值）
            tp_count = weighted_status.get('TP', 0)
            fp_count = weighted_status.get('FP', 0)
            fn_count = weighted_status.get('FN', 0)
            skip_count = weighted_status.get('SKIP', 0)
            
            if tp_count + fp_count + fn_count > 0:
                precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0
                recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0
                f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
                
                print(f"\n性能指标（基于加权值）:")
                print(f"  准确率 (Precision): {precision:.4f}")
                print(f"  召回率 (Recall): {recall:.4f}")
                print(f"  F1分数: {f1:.4f}")
                print(f"  跳过的纯字符串对比: {skip_count:.0f}")
                print(f"\n说明: 对于包含3个及以上数字的ground truth，其权重为数字个数")
        
        print("="*60 + "\n")


def main():
    """主函数"""
    # 配置路径
    ground_truth_csv = '/Users/caopengbo/Documents/code/porous_llm_extra/evaluation_results/combined_detailed_report.csv'
    json_dir = '/Volumes/mac_outstore/毕业/测试集文献/zhipu'
    output_csv = '/Users/caopengbo/Documents/code/porous_llm_extra/evaluation_results/rule_based_evaluation_results.csv'
    
    # 创建评估器
    evaluator = RuleBasedEvaluator(ground_truth_csv)
    
    # 执行评估
    results_df = evaluator.evaluate_directory(json_dir, output_csv)
    
    return results_df


if __name__ == '__main__':
    main()
