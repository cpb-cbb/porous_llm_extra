import json
import csv
from datetime import datetime
from pathlib import Path
from deepdiff import DeepDiff
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

# --- 配置 ---
EXTRACTED_DIR = 'extracted_results'  # 存放抽取结果的目录
GROUND_TRUTH_DIR = 'ground_truth'    # 存放基准数据的目录
OUTPUT_DIR = 'evaluation_reports'    # 存放评估报告的目录
# ---

console = Console()

def load_json(filepath):
    """加载 JSON 文件并处理可能的文件不存在错误"""
    #仅加载micro_features和ele_chem_info作为比对，因为工艺信息过于主观，且变化较大，容易引入误差
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {
                "micro_features": data.get("micro_features"),
                "ele_chem_info": data.get("ele_chem_info")
            }
    except FileNotFoundError:
        console.print(f"[bold red]错误: 文件未找到 -> {filepath}[/bold red]")
        return None
    except json.JSONDecodeError:
        console.print(f"[bold red]错误: 文件格式不是有效的 JSON -> {filepath}[/bold red]")
        return None

def count_total_facts(data):
    """递归地计算数据中的事实总数(叶节点数量)"""
    count = 0
    if isinstance(data, dict):
        for key, value in data.items():
            count += count_total_facts(value)
    elif isinstance(data, list):
        for item in data:
            count += count_total_facts(item)
    else:
        # 这是一个叶节点,即一个事实
        count = 1
    return count

def evaluate_single_file(extracted_path, ground_truth_path, output_dir):
    """评估单个文件对"""
    console.print(f"\n[bold cyan]正在评估: {extracted_path.name}[/bold cyan]")
    
    # 1. 加载数据
    extracted_data = load_json(extracted_path)
    ground_truth_data = load_json(ground_truth_path)
    
    if extracted_data is None or ground_truth_data is None:
        console.print(f"[bold red]跳过 {extracted_path.name}[/bold red]")
        return None

    # 2. 比较差异
    diff = DeepDiff(ground_truth_data, extracted_data, ignore_order=True, verbose_level=2)

    # 初始化指标和结果记录
    fp_count, fn_count = 0, 0
    evaluation_log = []

    # 3. 交互式评估差异
    
    # 3.1 处理新增项 (False Positives)
    if 'dictionary_item_added' in diff:
        for path in diff['dictionary_item_added']:
            value = diff['dictionary_item_added'][path]
            console.print(Panel(
                f"[bold]路径:[/bold] {path}\n[bold]抽取值:[/bold] {value}",
                title="[bold yellow]发现新增项 (Potential FP)[/bold yellow]",
                border_style="yellow"
            ))
            judgment = Prompt.ask("这是幻觉/错误抽取吗? (y/n/s for skip)", choices=['y', 'n', 's'], default='y')

            if judgment == 'y':
                fp_count += 1
                user_judgment = 'False Positive'
            elif judgment == 'n':
                 user_judgment = 'Correct (Ignored)'
            else:
                user_judgment = 'Skipped'
            
            evaluation_log.append({
                'Path': path,
                'Difference Type': 'Item Added',
                'Ground Truth Value': 'N/A',
                'Extracted Value': value,
                'User Judgment': user_judgment
            })

    # 3.2 处理缺失项 (False Negatives)
    if 'dictionary_item_removed' in diff:
        for path in diff['dictionary_item_removed']:
            value = diff['dictionary_item_removed'][path]
            console.print(Panel(
                f"[bold]路径:[/bold] {path}\n[bold]基准值:[/bold] {value}",
                title="[bold red]发现缺失项 (Potential FN)[/bold red]",
                border_style="red"
            ))
            judgment = Prompt.ask("这是漏报/未抽到吗? (y/n/s for skip)", choices=['y', 'n', 's'], default='y')
            
            if judgment == 'y':
                fn_count += 1
                user_judgment = 'False Negative'
            elif judgment == 'n':
                user_judgment = 'Correct (Ignored)'
            else:
                user_judgment = 'Skipped'
                
            evaluation_log.append({
                'Path': path,
                'Difference Type': 'Item Removed',
                'Ground Truth Value': value,
                'Extracted Value': 'N/A',
                'User Judgment': user_judgment
            })
            
    # 3.3 处理值变化 (FP + FN)
    if 'values_changed' in diff:
        for path, changes in diff['values_changed'].items():
            old_val, new_val = changes['old_value'], changes['new_value']
            console.print(Panel(
                f"[bold]路径:[/bold] {path}\n[bold red]基准值:[/bold red] {old_val}\n[bold yellow]抽取值:[/bold yellow] {new_val}",
                title="[bold magenta]发现值不匹配 (Potential FP & FN)[/bold magenta]",
                border_style="magenta"
            ))
            judgment = Prompt.ask("这是一个抽取错误吗? (y/n/s for skip)", choices=['y', 'n', 's'], default='y')

            if judgment == 'y':
                fp_count += 1
                fn_count += 1
                user_judgment = 'Value Mismatch (FP & FN)'
            elif judgment == 'n':
                user_judgment = 'Correct (Ignored)'
            else:
                user_judgment = 'Skipped'

            evaluation_log.append({
                'Path': path,
                'Difference Type': 'Value Changed',
                'Ground Truth Value': old_val,
                'Extracted Value': new_val,
                'User Judgment': user_judgment
            })

    # 4. 计算最终指标
    console.print("\n[bold cyan]评估完成，正在计算最终指标...[/bold cyan]")
    
    # 计算基准集中的事实总数
    total_facts_in_ground_truth = count_total_facts(ground_truth_data)
    
    # TP = 基准集总事实数 - 漏报数
    tp_count = total_facts_in_ground_truth - fn_count

    # 计算 Precision, Recall, F1
    precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0
    recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    # 5. 保存评估日志到 CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = output_dir / f'{extracted_path.stem}_report_{timestamp}.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Path', 'Difference Type', 'Ground Truth Value', 'Extracted Value', 'User Judgment']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(evaluation_log)
    console.print(f"[bold green]详细评估报告已保存到: {csv_filename}[/bold green]")

    # 6. 打印当前文件结果
    summary_panel = Panel(
        f"[bold]文件:[/bold] {extracted_path.name}\n"
        f"[bold]True Positives (TP):[/bold] {tp_count}\n"
        f"[bold]False Positives (FP):[/bold] {fp_count}\n"
        f"[bold]False Negatives (FN):[/bold] {fn_count}\n\n"
        f"[bold blue]Precision:[/bold blue] {precision:.4f}\n"
        f"[bold green]Recall:[/bold green]    {recall:.4f}\n"
        f"[bold yellow]F1-Score:[/bold yellow]  {f1_score:.4f}",
        title="[bold]单文件评估结果[/bold]",
        border_style="blue"
    )
    console.print(summary_panel)
    
    return {
        'filename': extracted_path.name,
        'tp': tp_count,
        'fp': fp_count,
        'fn': fn_count,
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score
    }

def evaluate_batch():
    """批量评估函数"""
    console.print("[bold cyan]开始批量信息抽取结果评估...[/bold cyan]")
    
    # 创建目录
    extracted_dir = Path(EXTRACTED_DIR)
    ground_truth_dir = Path(GROUND_TRUTH_DIR)
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)
    
    # 检查目录是否存在
    if not extracted_dir.exists():
        console.print(f"[bold red]错误: 抽取结果目录不存在 -> {extracted_dir}[/bold red]")
        return
    if not ground_truth_dir.exists():
        console.print(f"[bold red]错误: 基准数据目录不存在 -> {ground_truth_dir}[/bold red]")
        return
    
    # 获取所有 JSON 文件
    extracted_files = list(extracted_dir.glob('*.json'))
    
    if not extracted_files:
        console.print(f"[bold red]错误: 在 {extracted_dir} 中没有找到 JSON 文件[/bold red]")
        return
    
    console.print(f"[bold]找到 {len(extracted_files)} 个文件待评估[/bold]")
    
    # 批量评估
    results = []
    for extracted_file in extracted_files:
        # 查找对应的基准文件
        ground_truth_file = ground_truth_dir / extracted_file.name
        
        if not ground_truth_file.exists():
            console.print(f"[bold yellow]警告: 未找到对应的基准文件 -> {ground_truth_file}[/bold yellow]")
            continue
        
        result = evaluate_single_file(extracted_file, ground_truth_file, output_dir)
        if result:
            results.append(result)
    
    # 打印汇总结果
    if results:
        console.print("\n[bold cyan]=" * 50)
        console.print("批量评估汇总结果")
        console.print("=" * 50 + "[/bold cyan]\n")
        
        table = Table(title="所有文件评估指标")
        table.add_column("文件名", style="cyan")
        table.add_column("TP", justify="right", style="green")
        table.add_column("FP", justify="right", style="red")
        table.add_column("FN", justify="right", style="red")
        table.add_column("Precision", justify="right", style="blue")
        table.add_column("Recall", justify="right", style="green")
        table.add_column("F1-Score", justify="right", style="yellow")
        
        for r in results:
            table.add_row(
                r['filename'],
                str(r['tp']),
                str(r['fp']),
                str(r['fn']),
                f"{r['precision']:.4f}",
                f"{r['recall']:.4f}",
                f"{r['f1_score']:.4f}"
            )
        
        console.print(table)
        
        # 计算平均指标
        avg_precision = sum(r['precision'] for r in results) / len(results)
        avg_recall = sum(r['recall'] for r in results) / len(results)
        avg_f1 = sum(r['f1_score'] for r in results) / len(results)
        
        avg_panel = Panel(
            f"[bold blue]平均 Precision:[/bold blue] {avg_precision:.4f}\n"
            f"[bold green]平均 Recall:[/bold green]    {avg_recall:.4f}\n"
            f"[bold yellow]平均 F1-Score:[/bold yellow]  {avg_f1:.4f}",
            title="[bold]平均指标[/bold]",
            border_style="magenta"
        )
        console.print(avg_panel)
        
        # 保存汇总结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = output_dir / f'summary_{timestamp}.csv'
        with open(summary_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['filename', 'tp', 'fp', 'fn', 'precision', 'recall', 'f1_score']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        console.print(f"\n[bold green]汇总报告已保存到: {summary_file}[/bold green]")


if __name__ == "__main__":
    # 选择评估模式
    mode = Prompt.ask(
        "请选择评估模式",
        choices=['single', 'batch'],
        default='batch'
    )
    if mode == 'single':
        # 单文件评估 (保留原有功能)
        EXTRACTED_JSON_PATH = 'extracted_data.json'
        GROUND_TRUTH_JSON_PATH = 'ground_truth.json'
        OUTPUT_DIR_PATH = Path(OUTPUT_DIR)
        OUTPUT_DIR_PATH.mkdir(exist_ok=True)
        
        result = evaluate_single_file(
            Path(EXTRACTED_JSON_PATH),
            Path(GROUND_TRUTH_JSON_PATH),
            OUTPUT_DIR_PATH
        )
    else:
        # 批量评估,由于工艺信息复杂，默认跳过对工艺信息的评估，仅评估数值较多的微观结构以及电化学特征
        evaluate_batch()