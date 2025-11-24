
import os
from pathlib import Path
from typing import List, Dict, Tuple, Set
from envalue.envalue_test import flatten_json, get_agent_audit, generate_evaluation_report_strict
import json
import pandas as pd
from datetime import datetime


def load_progress(progress_file: str) -> Dict:
    """
    加载进度文件
    
    Args:
        progress_file: 进度文件路径
    
    Returns:
        包含已处理文件和结果的字典
    """
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  加载进度文件失败: {str(e)}")
            return {"processed_files": [], "results": []}
    return {"processed_files": [], "results": []}


def save_progress(progress_file: str, processed_files: List[str], results: List[Dict]):
    """
    保存进度到临时文件
    
    Args:
        progress_file: 进度文件路径
        processed_files: 已处理的文件名列表
        results: 评估结果列表
    """
    progress_data = {
        "processed_files": processed_files,
        "results": results,
        "last_update": datetime.now().isoformat()
    }
    
    try:
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️  保存进度失败: {str(e)}")


def save_single_result(result_file: str, filename: str, metrics: Dict, df_report: pd.DataFrame):
    """
    保存单个文件的评估结果到临时JSON
    
    Args:
        result_file: 结果文件路径
        filename: 文件名
        metrics: 评估指标
        df_report: 详细报告DataFrame
    """
    result = {
        "filename": filename,
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics,
        "detailed_report": df_report.to_dict(orient='records')
    }
    
    try:
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️  保存结果文件失败: {str(e)}")
def load_json_files(directory_path: str) -> List[Dict]:
    """
    从指定目录加载所有 JSON 文件
    
    Args:
        directory_path: JSON 文件所在目录路径
    
    Returns:
        包含所有 JSON 数据的列表
    """
    json_files = []
    directory = Path(directory_path)
    
    for json_file in directory.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['_filename'] = json_file.name  # 记录文件名
                json_files.append(data)
            print(f"✓ 成功加载: {json_file.name}")
        except Exception as e:
            print(f"✗ 加载失败 {json_file.name}: {str(e)}")
    
    return json_files

def process_single_file(file_data: Dict, file_index: int) -> Tuple[pd.DataFrame, Dict, str]:
    """
    处理单个 JSON 文件
    
    Args:
        file_data: 包含 final_result 和 content 的 JSON 数据
        file_index: 文件索引
    
    Returns:
        (详细报告 DataFrame, 评估指标, 文件名)
    """
    filename = file_data.get('_filename', f'file_{file_index}')
    
    # 提取必要字段
    extracted_data = file_data.get('final_result', {})
    source_text = file_data.get('content', '')
    
    if not extracted_data:
        print(f"⚠️  {filename}: final_result 为空")
        return None, None, filename
    
    if not source_text:
        print(f"⚠️  {filename}: content 为空")
        return None, None, filename
    
    # 1. 扁平化数据
    flat_extracted = flatten_json(extracted_data)
    
    # 2. 调用 Agent 进行审计
    print(f"🔍 正在审计 {filename}...")
    agent_output = get_agent_audit(source_text, flat_extracted)
    
    # 3. 生成评估报告
    df_report, metrics = generate_evaluation_report_strict(extracted_data, agent_output)
    
    # 添加文件名列
    df_report['File'] = filename
    
    return df_report, metrics, filename

def batch_evaluate_json_files(directory_path: str, output_dir: str = "./evaluation_results", resume: bool = True):
    """
    批量评估多个 JSON 文件（支持断点续传）
    
    Args:
        directory_path: JSON 文件所在目录
        output_dir: 评估报告输出目录
        resume: 是否从上次中断处继续（默认True）
    """
    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 进度和临时结果目录
    progress_dir = os.path.join(output_dir, ".progress")
    temp_results_dir = os.path.join(output_dir, ".temp_results")
    Path(progress_dir).mkdir(parents=True, exist_ok=True)
    Path(temp_results_dir).mkdir(parents=True, exist_ok=True)
    
    progress_file = os.path.join(progress_dir, "progress.json")
    
    # 1. 加载所有 JSON 文件
    print(f"\n{'='*60}")
    print(f"📂 从目录加载 JSON 文件: {directory_path}")
    print(f"{'='*60}\n")
    
    json_files = load_json_files(directory_path)
    #截断到前20个
    json_files = json_files[:20]
    if not json_files:
        print("❌ 未找到任何 JSON 文件！")
        return
    
    print(f"\n✅ 共加载 {len(json_files)} 个文件\n")
    
    # 2. 加载进度（如果启用断点续传）
    processed_files_set: Set[str] = set()
    all_results = []
    
    if resume:
        progress_data = load_progress(progress_file)
        processed_files_set = set(progress_data.get("processed_files", []))
        all_results = progress_data.get("results", [])
        
        if processed_files_set:
            print(f"📋 从上次进度恢复: 已处理 {len(processed_files_set)} 个文件")
            print(f"   继续处理剩余 {len(json_files) - len(processed_files_set)} 个文件\n")
    
    # 3. 处理每个文件
    all_reports = []
    all_metrics = []
    skipped_count = 0
    
    for i, file_data in enumerate(json_files, 1):
        filename = file_data.get('_filename', f'file_{i}')
        
        # 检查是否已处理
        if filename in processed_files_set:
            skipped_count += 1
            print(f"⏭️  跳过已处理文件 [{i}/{len(json_files)}]: {filename}")
            
           # 从临时结果加载数据
            temp_result_file = os.path.join(temp_results_dir, f"{Path(filename).stem}_result.json")
            if os.path.exists(temp_result_file):
                try:
                    with open(temp_result_file, 'r', encoding='utf-8') as f:
                        cached_result = json.load(f)
                        # 确保缓存的 metrics 中包含 File 字段
                        cached_metrics = cached_result['metrics']
                        if 'File' not in cached_metrics:
                            cached_metrics['File'] = filename
                        all_metrics.append(cached_metrics)
                        all_reports.append(pd.DataFrame(cached_result['detailed_report']))
                except Exception as e:
                    print(f"   ⚠️  加载缓存失败: {str(e)}")
            continue
        
        print(f"\n{'='*60}")
        print(f"📄 处理文件 [{i}/{len(json_files)}] (新处理: {i - skipped_count})")
        print(f"{'='*60}\n")
        
        try:
            df_report, metrics, filename = process_single_file(file_data, i)
            
            if df_report is not None and metrics is not None:
                all_reports.append(df_report)
                # 添加文件名到 metrics
                metrics['File'] = filename
                all_metrics.append(metrics)
                
                # 保存单个文件的详细报告 CSV
                report_filename = f"{Path(filename).stem}_report.csv"
                report_path = os.path.join(output_dir, report_filename)
                df_report.to_csv(report_path, index=False, encoding='utf-8-sig')
                print(f"💾 详细报告已保存: {report_path}")
                
                # 保存临时JSON结果
                temp_result_file = os.path.join(temp_results_dir, f"{Path(filename).stem}_result.json")
                save_single_result(temp_result_file, filename, metrics, df_report)
                print(f"💾 临时结果已保存: {temp_result_file}")
                
                # 更新进度
                processed_files_set.add(filename)
                all_results.append({
                    "filename": filename,
                    "metrics": metrics,
                    "processed_at": datetime.now().isoformat()
                })
                save_progress(progress_file, list(processed_files_set), all_results)
                print(f"✅ 进度已保存 ({len(processed_files_set)}/{len(json_files)})")
            else:
                print(f"⚠️  跳过文件: {filename}")
                # 仍然标记为已处理，避免重复尝试
                processed_files_set.add(filename)
                save_progress(progress_file, list(processed_files_set), all_results)
                
        except Exception as e:
            print(f"❌ 处理文件出错 {filename}: {str(e)}")
            print(f"   进度已保存，可稍后重新运行继续处理")
            # 不标记为已处理，以便下次重试
            continue
    
    # 4. 生成汇总报告
    if all_reports and all_metrics:
        print(f"\n{'='*60}")
        print("📊 生成汇总报告")
        print(f"{'='*60}\n")
        
        # 合并所有详细报告
        combined_report = pd.concat(all_reports, ignore_index=True)
        combined_report_path = os.path.join(output_dir, "combined_detailed_report.csv")
        combined_report.to_csv(combined_report_path, index=False, encoding='utf-8-sig')
        print(f"✅ 合并详细报告: {combined_report_path}")
        
        # 生成指标汇总表
        metrics_df = pd.DataFrame(all_metrics)
        metrics_summary_path = os.path.join(output_dir, "metrics_summary.csv")
        metrics_df.to_csv(metrics_summary_path, index=False, encoding='utf-8-sig')
        print(f"✅ 指标汇总表: {metrics_summary_path}")
        
        # 保存汇总JSON
        summary_json_path = os.path.join(output_dir, "summary.json")
        summary_data = {
            "total_files": len(json_files),
            "processed_files": len(processed_files_set),
            "timestamp": datetime.now().isoformat(),
            "average_metrics": {
                "precision": float(metrics_df['Precision'].mean()),
                "recall": float(metrics_df['Recall'].mean()),
                "f1_score": float(metrics_df['F1_Score'].mean())
            },
            "total_counts": {
                "TP": int(metrics_df['TP'].sum()),
                "FP": int(metrics_df['FP (Inaccurate Predictions)'].sum()),
                "FN": int(metrics_df['FN (Missed Ground Truths)'].sum()),
                "TN": int(metrics_df['TN (Correctly Empty)'].sum())
            }
        }
        with open(summary_json_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        print(f"✅ 汇总JSON: {summary_json_path}")
        
        # 打印汇总统计
        print("\n" + "="*60)
        print("📈 汇总统计")
        print("="*60)
        print(f"\n平均 Precision: {metrics_df['Precision'].mean():.2f}%")
        print(f"平均 Recall: {metrics_df['Recall'].mean():.2f}%")
        print(f"平均 F1 Score: {metrics_df['F1_Score'].mean():.2f}%")
        print(f"\n总 TP: {metrics_df['TP'].sum()}")
        print(f"总 FP: {metrics_df['FP (Inaccurate Predictions)'].sum()}")
        print(f"总 FN: {metrics_df['FN (Missed Ground Truths)'].sum()}")
        print(f"总 TN: {metrics_df['TN (Correctly Empty)'].sum()}")
        
        # 显示各文件的指标
        print("\n" + "="*60)
        print("📋 各文件评估结果")
        print("="*60)
        print(metrics_df[['File', 'Precision', 'Recall', 'F1_Score']].to_string(index=False))
    
    print(f"\n{'='*60}")
    print("✨ 批量评估完成！")
    print(f"{'='*60}\n")
    
    # 5. 清理进度文件（可选）
    if len(processed_files_set) == len(json_files):
        print("🧹 所有文件处理完成，可以删除临时进度文件")
        print(f"   进度目录: {progress_dir}")
        print(f"   临时结果目录: {temp_results_dir}")
        print(f"   如需清理，请手动删除这些目录\n")

# ================= 使用示例 =================

if __name__ == "__main__":
    # 方式1: 批量处理目录中的所有 JSON 文件（支持断点续传）
    json_directory = "/Volumes/mac_outstore/毕业/测试集文献/zhipu"  # 修改为你的 JSON 文件目录
    output_directory = "./evaluation_results"  # 修改为输出目录
    
    # resume=True: 从上次中断处继续
    # resume=False: 从头开始处理（会覆盖之前的进度）
    batch_evaluate_json_files(json_directory, output_directory, resume=True)
    
    # 方式2: 处理单个文件（保留原有功能）
    # with open("/Volumes/mac_outstore/毕业/测试集文献/zhipu/10.1016_j.arabjc.2018.08.009_extracted.json", 'r', encoding='utf-8') as f:
    #     data = json.load(f)
    #     extracted_data = data.get('final_result', {})
    #     source_text = data.get('content', '')
    #     
    #     flat_extracted = flatten_json(extracted_data)
    #     
    #     agent_output = get_agent_audit(source_text, flat_extracted)
    #     df_report, metrics = generate_evaluation_report_strict(extracted_data, agent_output)
    #     
    #     print("=== 评估指标 ===")
    #     print(json.dumps(metrics, indent=2, ensure_ascii=False))
    #     df_report.to_csv("single_file_report.csv", index=False, encoding='utf-8-sig')