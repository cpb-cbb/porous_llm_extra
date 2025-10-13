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
# 请根据你的实际路径修改这些变量
EXTRACTED_DIR = '/Volumes/mac_outstore/毕业/测试集文献/zhipu'
GROUND_TRUTH_DIR = '/Volumes/mac_outstore/毕业/测试集文献/base_evalue_data'
OUTPUT_DIR = '/Volumes/mac_outstore/毕业/测试集文献/evaluation_reports2'
PROGRESS_FILE = '/Volumes/mac_outstore/毕业/测试集文献/evaluation_reports2/evaluation_progress2.json'
# ---

console = Console()

def load_progress():
    """加载评估进度记录"""
    progress_path = Path(PROGRESS_FILE)
    if progress_path.exists():
        try:
            with open(progress_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            console.print(f"[bold red]警告: 进度文件 {PROGRESS_FILE} 格式错误, 将重新开始评估。[/bold red]")
            return {}
    return {}

def save_progress(progress):
    """保存评估进度记录"""
    progress_path = Path(PROGRESS_FILE)
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    with open(progress_path, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)

def load_json(filepath):
    """加载 JSON 文件并处理可能的文件不存在或格式错误"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 为保证比较的一致性，只关注这两个关键字段
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
        # 如果字典为空，也算0个事实
        if not data:
            return 0
        for key, value in data.items():
            count += count_total_facts(value)
    elif isinstance(data, list):
        # 如果列表为空，也算0个事实
        if not data:
            return 0
        for item in data:
            count += count_total_facts(item)
    # 过滤掉 None 和空字符串等无效叶节点
    elif data is not None and data != "":
        count = 1
    return count

def evaluate_single_file(extracted_path, ground_truth_path, output_dir):
    """评估单个文件对 (对 values_changed 提供精细控制)"""
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

    console.print("\n[bold]请根据以下差异进行判断:[/bold]")

    # 3.1 处理新增项 (Potential False Positives) - (此部分代码不变)
    if 'dictionary_item_added' in diff:
        for path in diff['dictionary_item_added']:
            value = diff['dictionary_item_added'][path]
            facts_count = count_total_facts(value)
            if facts_count == 0: continue

            console.print(Panel(
                f"[bold]路径:[/bold] {path}\n[bold]抽取值:[/bold] {value}\n[bold]包含事实数:[/bold] {facts_count}",
                title="[bold yellow]发现新增项 (Potential FP - 基准中没有)[/bold yellow]",
                border_style="yellow"
            ))
            judgment = Prompt.ask(
                f"这是错误的抽取吗? 输入错误数量(0-{facts_count}), 或 y(全部错误)/n(全部正确)/s(跳过)",
                default='y'
            )

            error_count = 0
            user_judgment = 'Skipped'
            if judgment.lower() == 'y':
                error_count = facts_count
                user_judgment = f'False Positive ({facts_count}条)'
            elif judgment.lower() == 'n':
                error_count = 0
                user_judgment = f'Correctly Added (不计入FP, 基准需更新)'
            elif judgment.lower() == 's':
                pass
            elif judgment.isdigit() and 0 <= int(judgment) <= facts_count:
                error_count = int(judgment)
                user_judgment = f'Partial ({error_count} 错误, {facts_count - error_count} 正确新增)'
            else:
                console.print("[bold red]输入无效, 按全部错误处理[/bold red]")
                error_count = facts_count
                user_judgment = f'False Positive ({facts_count}条)'

            if judgment.lower() != 's':
                fp_count += error_count

            evaluation_log.append({
                'Path': path, 'Difference Type': 'Item Added (Potential FP)',
                'Ground Truth Value': 'N/A', 'Extracted Value': value,
                'User Judgment': user_judgment
            })

    # 3.2 处理缺失项 (Potential False Negatives) - (此部分代码不变)
    if 'dictionary_item_removed' in diff:
        for path in diff['dictionary_item_removed']:
            value = diff['dictionary_item_removed'][path]
            facts_count = count_total_facts(value)
            if facts_count == 0: continue

            console.print(Panel(
                f"[bold]路径:[/bold] {path}\n[bold]基准值:[/bold] {value}\n[bold]包含事实数:[/bold] {facts_count}",
                title="[bold red]发现缺失项 (Potential FN - 抽取结果中没有)[/bold red]",
                border_style="red"
            ))
            judgment = Prompt.ask(
                f"这是真正的遗漏吗? 输入遗漏数量(0-{facts_count}), 或 y(全部遗漏)/n(不是遗漏)/s(跳过)",
                default='y'
            )

            missing_count = 0
            user_judgment = 'Skipped'
            if judgment.lower() == 'y':
                missing_count = facts_count
                user_judgment = f'False Negative ({facts_count}条)'
            elif judgment.lower() == 'n':
                missing_count = 0
                user_judgment = f'Not a real miss (基准可能有问题)'
            elif judgment.lower() == 's':
                pass
            elif judgment.isdigit() and 0 <= int(judgment) <= facts_count:
                missing_count = int(judgment)
                user_judgment = f'Partial ({missing_count} 遗漏, {facts_count - missing_count} 不是遗漏)'
            else:
                console.print("[bold red]输入无效, 按全部遗漏处理[/bold red]")
                missing_count = facts_count
                user_judgment = f'False Negative ({facts_count}条)'

            if judgment.lower() != 's':
                fn_count += missing_count

            evaluation_log.append({
                'Path': path, 'Difference Type': 'Item Removed (Potential FN)',
                'Ground Truth Value': value, 'Extracted Value': 'N/A',
                'User Judgment': user_judgment
            })

    # 3.3 处理值变化 (Potential FP & FN) - (*** 这是修改的核心部分 ***)
    if 'values_changed' in diff:
        for path, changes in diff['values_changed'].items():
            old_val, new_val = changes['old_value'], changes['new_value']
            
            # 以基准值中的事实数量为准
            facts_count = count_total_facts(old_val)
            if facts_count == 0: # 如果基准值是None或空，而抽取值有内容，这应该被DeepDiff归为Item Added，但以防万一
                # 这种情况可以视为一个FP
                fp_facts = count_total_facts(new_val)
                fp_count += fp_facts
                evaluation_log.append({
                    'Path': path, 'Difference Type': 'Value Changed (GT is Empty)',
                    'Ground Truth Value': old_val, 'Extracted Value': new_val,
                    'User Judgment': f'Ground truth is empty, counted as {fp_facts} FP'
                })
                continue
            
            console.print(Panel(
                f"[bold]路径:[/bold] {path}\n"
                f"[bold red]基准值:[/bold red] {old_val}\n"
                f"[bold yellow]抽取值:[/bold yellow] {new_val}\n"
                f"[bold]基准包含事实数:[/bold] {facts_count}",
                title="[bold magenta]发现值不匹配 (Potential FP & FN)[/bold magenta]",
                border_style="magenta"
            ))

            judgment = Prompt.ask(
                f"在这 {facts_count} 个基准事实中, 有多少个是错误的? 输入错误数量(0-{facts_count}), 或 s(跳过)",
                default=str(facts_count) # 默认全部错误
            )
            
            error_count = 0
            user_judgment = 'Skipped'
            if judgment.lower() == 's':
                pass
            elif judgment.isdigit() and 0 <= int(judgment) <= facts_count:
                error_count = int(judgment)
                correct_count = facts_count - error_count
                user_judgment = f'Partial ({error_count} 错误, {correct_count} 正确)'
            else:
                console.print("[bold red]输入无效, 按全部错误处理[/bold red]")
                error_count = facts_count
                user_judgment = f'All Mismatched ({facts_count}条)'

            if judgment.lower() != 's':
                # 每一个错误都同时是一个 FP 和一个 FN
                fp_count += error_count
                fn_count += error_count
            
            evaluation_log.append({
                'Path': path, 'Difference Type': 'Value Changed (Potential FP & FN)',
                'Ground Truth Value': old_val, 'Extracted Value': new_val,
                'User Judgment': user_judgment
            })
            
    # 4. 计算最终指标 - (此部分代码不变)
    console.print("\n[bold cyan]评估完成, 正在计算最终指标...[/bold cyan]")

    total_gt_facts = count_total_facts(ground_truth_data)
    
    tp_count = max(0, total_gt_facts - fn_count)
    
    precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0
    recall = tp_count / total_gt_facts if total_gt_facts > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    # 5. 保存评估日志到 CSV - (此部分代码不变)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = output_dir / f'{extracted_path.stem}_report_{timestamp}.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Path', 'Difference Type', 'Ground Truth Value', 'Extracted Value', 'User Judgment']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(evaluation_log)
    console.print(f"[bold green]详细评估报告已保存到: {csv_filename}[/bold green]")

    # 6. 打印当前文件结果 - (此部分代码不变)
    summary_panel = Panel(
        f"[bold]文件:[/bold] {extracted_path.name}\n"
        f"[bold]基准集总事实数 (Total GT Facts):[/bold] {total_gt_facts}\n\n"
        f"[bold green]True Positives (TP):[/bold green] {tp_count}  (计算得出: Total GT - FN)\n"
        f"[bold red]False Positives (FP):[/bold red] {fp_count} (来自新增项和值变化)\n"
        f"[bold red]False Negatives (FN):[/bold red] {fn_count} (来自缺失项和值变化)\n\n"
        f"[bold blue]Precision:[/bold blue] {precision:.4f}\n"
        f"[bold green]Recall:[/bold green]    {recall:.4f}\n"
        f"[bold yellow]F1-Score:[/bold yellow]  {f1_score:.4f}",
        title="[bold]单文件评估结果 (修正后逻辑)[/bold]",
        border_style="blue"
    )
    console.print(summary_panel)

    return {
        'filename': extracted_path.name,
        'total_gt_facts': total_gt_facts,
        'tp': tp_count,
        'fp': fp_count,
        'fn': fn_count,
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'timestamp': timestamp
    }

def evaluate_batch():
    """批量评估函数"""
    console.print("[bold cyan]开始批量信息抽取结果评估...[/bold cyan]")
    
    extracted_dir = Path(EXTRACTED_DIR)
    ground_truth_dir = Path(GROUND_TRUTH_DIR)
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    if not extracted_dir.is_dir() or not ground_truth_dir.is_dir():
        console.print(f"[bold red]错误: 请确保抽取结果目录 ({extracted_dir}) 和基准数据目录 ({ground_truth_dir}) 均存在。[/bold red]")
        return
    
    progress = load_progress()
    extracted_files = sorted(list(extracted_dir.glob('*.json')))
    
    if not extracted_files:
        console.print(f"[bold red]错误: 在 {extracted_dir} 中没有找到任何 JSON 文件。[/bold red]")
        return
    
    evaluated_count = sum(1 for f in extracted_files if f.name in progress)
    pending_count = len(extracted_files) - evaluated_count
    
    console.print(f"[bold]找到 {len(extracted_files)} 个文件: "
                  f"[green]{evaluated_count} 个已评估[/green], "
                  f"[yellow]{pending_count} 个待评估[/yellow][/bold]")
    
    if evaluated_count > 0:
        reevaluate = Prompt.ask(
            "是否重新评估已评估的文件? (这将清空现有进度)",
            choices=['y', 'n'], default='n'
        )
        if reevaluate == 'y':
            progress = {}
            console.print("[bold yellow]已清空评估进度, 将重新评估所有文件。[/bold yellow]")
    
    results = [progress[f.name] for f in extracted_files if f.name in progress]
    
    for i, extracted_file in enumerate(extracted_files, 1):
        if extracted_file.name in progress:
            console.print(f"\n[bold green]跳过已评估文件 ({i}/{len(extracted_files)}): {extracted_file.name}[/bold green]")
            continue
        
        ground_truth_file = ground_truth_dir / extracted_file.name
        if not ground_truth_file.exists():
            console.print(f"[bold yellow]警告: 未找到对应的基准文件, 跳过 -> {ground_truth_file}[/bold yellow]")
            continue
        
        console.print(f"\n[bold]进度: {i}/{len(extracted_files)}[/bold]")
        result = evaluate_single_file(extracted_file, ground_truth_file, output_dir)
        
        if result:
            results.append(result)
            progress[extracted_file.name] = result
            save_progress(progress)
            console.print(f"[bold green]✓ 已保存评估进度[/bold green]")
    
    if results:
        console.print("\n[bold cyan]" + "=" * 60)
        console.print(" " * 20 + "批量评估汇总结果")
        console.print("=" * 60 + "[/bold cyan]\n")
        
        table = Table(title="所有文件评估指标 (宏观指标)")
        table.add_column("文件名", style="cyan", no_wrap=True)
        table.add_column("总事实数", justify="right")
        table.add_column("TP", justify="right", style="green")
        table.add_column("FP", justify="right", style="red")
        table.add_column("FN", justify="right", style="magenta")
        table.add_column("Precision", justify="right", style="blue")
        table.add_column("Recall", justify="right", style="green")
        table.add_column("F1-Score", justify="right", style="yellow")
        
        for r in results:
            table.add_row(
                r['filename'], str(r['total_gt_facts']), str(r['tp']),
                str(r['fp']), str(r['fn']), f"{r['precision']:.4f}",
                f"{r['recall']:.4f}", f"{r['f1_score']:.4f}"
            )
        console.print(table)
        
        # 宏观平均 (Macro Average)
        avg_precision = sum(r['precision'] for r in results) / len(results)
        avg_recall = sum(r['recall'] for r in results) / len(results)
        avg_f1 = sum(r['f1_score'] for r in results) / len(results)
        
        # 微观平均 (Micro Average)
        total_tp = sum(r['tp'] for r in results)
        total_fp = sum(r['fp'] for r in results)
        total_fn = sum(r['fn'] for r in results)
        total_gt = sum(r['total_gt_facts'] for r in results)
        
        micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        micro_recall = total_tp / total_gt if total_gt > 0 else 0
        micro_f1 = 2 * (micro_precision * micro_recall) / (micro_precision + micro_recall) if (micro_precision + micro_recall) > 0 else 0

        avg_panel = Panel(
            f"[bold]宏观平均 (Macro Average):[/bold] (对每个文件的指标求平均)\n"
            f"[blue]  - 平均 Precision:[/blue] {avg_precision:.4f}\n"
            f"[green]  - 平均 Recall:   [/green] {avg_recall:.4f}\n"
            f"[yellow]  - 平均 F1-Score:  [/yellow] {avg_f1:.4f}\n\n"
            f"[bold]微观平均 (Micro Average):[/bold] (汇总所有事实后计算一次指标)\n"
            f"[blue]  - 总体 Precision:[/blue] {micro_precision:.4f} (Total TP / (Total TP + Total FP))\n"
            f"[green]  - 总体 Recall:   [/green] {micro_recall:.4f} (Total TP / Total GT Facts)\n"
            f"[yellow]  - 总体 F1-Score:  [/yellow] {micro_f1:.4f}",
            title="[bold]总体平均指标[/bold]",
            border_style="magenta"
        )
        console.print(avg_panel)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = output_dir / f'summary_report_{timestamp}.csv'
        with open(summary_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['filename', 'total_gt_facts', 'tp', 'fp', 'fn', 'precision', 'recall', 'f1_score']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(results)
            writer.writerow({})
            writer.writerow({'filename': 'MICRO_AVERAGE_TOTALS', 'total_gt_facts': total_gt, 'tp': total_tp, 'fp': total_fp, 'fn': total_fn})
            writer.writerow({'filename': 'MICRO_AVERAGE_METRICS', 'precision': micro_precision, 'recall': micro_recall, 'f1_score': micro_f1})
            writer.writerow({'filename': 'MACRO_AVERAGE_METRICS', 'precision': avg_precision, 'recall': avg_recall, 'f1_score': avg_f1})
        console.print(f"\n[bold green]汇总报告已保存到: {summary_file}[/bold green]")
    else:
        console.print("[bold yellow]没有可供汇总的结果。[/bold yellow]")

if __name__ == "__main__":
    mode = Prompt.ask(
        "请选择评估模式",
        choices=['single', 'batch'],
        default='batch'
    )
    if mode == 'single':
        extracted_path_str = Prompt.ask("请输入抽取的JSON文件路径")
        gt_path_str = Prompt.ask("请输入对应的基准JSON文件路径")
        
        extracted_path = Path(extracted_path_str)
        gt_path = Path(gt_path_str)
        
        if not extracted_path.exists() or not gt_path.exists():
            console.print("[bold red]错误: 一个或两个文件路径无效。[/bold red]")
        else:
            output_dir_path = Path(OUTPUT_DIR)
            output_dir_path.mkdir(exist_ok=True, parents=True)
            evaluate_single_file(extracted_path, gt_path, output_dir_path)
    else:
        evaluate_batch()