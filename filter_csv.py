"""
CSV过滤脚本
读取评估CSV文件，使用字段模版过滤掉幻觉字段，重新计算F1分数
"""

import argparse
import sys
from pathlib import Path
from servers.utils.field_template import filter_csv_and_recalculate


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="过滤CSV文件中的幻觉字段并重新计算F1分数",
        epilog="示例: python filter_csv.py evaluation_results/combined_detailed_report.csv"
    )
    parser.add_argument(
        "input_csv",
        type=str,
        help="输入CSV文件路径（combined_detailed_report.csv格式）"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="输出CSV文件路径（默认为输入文件名_filtered.csv）"
    )
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    input_path = Path(args.input_csv)
    if not input_path.exists():
        print(f"❌ 错误: 输入文件不存在: {args.input_csv}")
        sys.exit(1)
    
    # 执行过滤和重新计算
    try:
        result = filter_csv_and_recalculate(
            input_csv_path=args.input_csv,
            output_csv_path=args.output
        )
        
        print("\n✅ 处理完成!")
        
    except Exception as e:
        print(f"\n❌ 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
