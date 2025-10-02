# -*- coding: utf-8 -*-

import os
import time
import pandas as pd
import re
import random
import json
from tqdm import tqdm
from zai import ZhipuAiClient
from servers.utils import TextProcess  # 假设这个模块能正确读取PDF

# --- 全局配置 (Global Configuration) ---

# ZhipuAI API 配置
api_key = os.environ.get('ZHIPUAI_API_KEY')
if not api_key:
    print("错误：未设置 ZHIPUAI_API_KEY 环境变量。")
    exit()
client = ZhipuAiClient(api_key=api_key)

MODEL_VERSION = "glm-4.5"
API_RETRY_DELAY = 10
API_MAX_RETRIES = 3

# 文件路径配置
PDF_DIRECTORY = "/Volumes/mac_outstore/毕业/jsol文献/biomass_super_2000"
CSV_FILE_PATH = "/Users/caopengbo/Documents/code/porous_llm_extra/datas/evalue_csv.csv"
OUTPUT_CSV_PATH = "datas/outputs/evaluation_results_with_reasons.csv" # 新的输出文件名
PROGRESS_FILE_PATH = "datas/outputs/evaluation_progress.json"

# 抽样配置
SAMPLE_SIZE = 200

# --- 辅助函数 (Helper Functions) ---

def parse_non_streaming_response(response):
    """解析非流式响应"""
    try:
        response_text = response.choices[0].message.content
        return response_text.strip()
    except (AttributeError, IndexError, TypeError) as e:
        print(f"解析响应时出错: {e}")
        print(f"原始响应: {response}")
        return None

def sanitize_doi_for_filename(doi: str) -> str:
    """清洗DOI，使其可以作为文件名进行安全查找。"""
    return re.sub(r'[\/\:\*\?\"\<\>\|]', '_', doi)

def find_pdf_by_doi(doi: str, directory: str) -> str | None:
    """根据DOI在指定目录中查找对应的PDF文件。"""
    sanitized_doi = sanitize_doi_for_filename(doi)
    for ext in ['.pdf', '.txt', '.json']:
        expected_filename = f"{sanitized_doi}{ext}"
        full_path = os.path.join(directory, expected_filename)
        if os.path.exists(full_path):
            print(f"找到文件: {full_path}")
            return full_path
    print(f"警告：未能找到与 DOI '{doi}' (文件名: {sanitized_doi}) 对应的文件。")
    return None

def evaluate_with_llm(original_text: str, extracted_data: str) -> tuple[str, str]:
    """
    调用LLM判断数据有效性，并返回结果和原因。
    返回一个元组: (评估结果, 原因)
    """
    prompt = f"""
请你扮演一个严格的学术信息评估专家。你的任务是根据提供的原文，判断提取出的样本的物理化学性质以及电化学性质信息是否准确、完整且得到了原文的支撑。

**评估标准:**
1.  **准确性**: 提取的每个数据点都必须在原文中有明确的支持
2.  **非虚构性**: 不得包含任何原文未提及的推断或虚构信息。
3.  **正确性**: 相应样本的数值、单位和材料名称必须与原文完全对应，不得与其他样本名称对应的数值混淆。
4.  **完整性**: 如果原文中缺少某些数据点，则提取的信息也确实没有则算对

---
**【原文内容】**
{original_text}
code
Code
---
**【提取的信息】**
{extracted_data}
code
Code
---
**输出要求:**
请严格按照以下 JSON 格式输出你的评估结果，不要包含任何额外的解释或格式。
{{
  "evaluation": "T",
  "reason": "此处填写你的判断理由。如果为 T，请说明信息得到了原文的充分支持；如果为 F，请指出具体哪项信息不准确、缺失或无法在原文中找到依据。"
}}

**示例输出:**
如果信息准确:
{{
  "evaluation": "T",
  "reason": "所有提取的数值、单位和材料名称均与原文完全对应。"
}}

如果信息不准确:
{{
  "evaluation": "F",
  "reason": "提取的比表面积为 850 m²/g，但原文中对应材料的数据是 805 m²/g。"
}}

**你的评估结果 (请严格使用JSON格式):**
"""
    current_retry = 0
    while current_retry < API_MAX_RETRIES:
        try:
            messages = [{"role": "user", "content": prompt}]
            response = client.chat.completions.create(
                model=MODEL_VERSION,
                messages=messages,
                top_p=0.7,
                temperature=0.1,
                max_tokens=8000,
                stream=False
            )
            response_text = parse_non_streaming_response(response)

            # 解析LLM返回的JSON
            try:
                # 找到JSON对象的部分，防止模型在前后添加额外字符
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if not json_match:
                    raise json.JSONDecodeError("未找到有效的JSON对象", response_text, 0)
                
                parsed_json = json.loads(json_match.group(0))
                evaluation = parsed_json.get("evaluation")
                reason = parsed_json.get("reason", "无原因提供")

                print(f"LLM 返回的评估结果: '{evaluation}', 原因: '{reason}'")
                if evaluation in ['T', 'F']:
                    return evaluation, reason
                else:
                    print(f"警告：LLM返回了非预期的 evaluation 值 '{evaluation}'，重试中...")

            except (json.JSONDecodeError, AttributeError) as json_e:
                print(f"警告：无法解析LLM返回的JSON。错误: {json_e}。返回内容: '{response_text}'，重试中...")

            current_retry += 1
            time.sleep(API_RETRY_DELAY * current_retry)

        except Exception as e:
            print(f"调用LLM API时出错: {e}")
            current_retry += 1
            if current_retry < API_MAX_RETRIES:
                print(f"正在重试 ({current_retry}/{API_MAX_RETRIES})...")
                time.sleep(API_RETRY_DELAY * current_retry)

    print("API 调用失败达到最大重试次数。")
    return 'unknown', 'API调用失败或返回了无效格式。'

# --- 进度管理函数 ---
def save_progress(processed_indices, results, sample_indices):
    """将进度保存到JSON文件"""
    progress = {
        'processed_indices': processed_indices,
        'results': results,
        'sample_indices': sample_indices
    }
    try:
        with open(PROGRESS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=4)
    except IOError as e:
        print(f"错误：无法写入进度文件 {PROGRESS_FILE_PATH}: {e}")

def load_progress():
    """从JSON文件加载进度"""
    if os.path.exists(PROGRESS_FILE_PATH):
        try:
            with open(PROGRESS_FILE_PATH, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                print(f"检测到中断的进度，已从 {PROGRESS_FILE_PATH} 加载。")
                return progress.get('processed_indices', []), progress.get('results', []), progress.get('sample_indices', [])
        except (IOError, json.JSONDecodeError) as e:
            print(f"警告：无法读取或解析进度文件，将重新开始。错误: {e}")
    return [], [], []

# --- 主逻辑 (Main Logic) ---
def main():
    """主执行函数"""
    print("开始执行评估代理...")

    # 1. 读取CSV文件
    try:
        df = pd.read_csv(CSV_FILE_PATH)
        print(f"成功读取CSV文件，共 {len(df)} 行。")
    except FileNotFoundError:
        print(f"错误：无法找到CSV文件 at {CSV_FILE_PATH}")
        return

    # 2. 加载或创建样本
    processed_indices, results, sample_indices = load_progress()
    
    if sample_indices:
        sample_df = df.loc[sample_indices]
        print(f"已从进度文件恢复 {len(sample_df)} 行的评估样本。")
    else:
        if len(df) <= SAMPLE_SIZE:
            sample_df = df
        else:
            sample_df = df.sample(n=SAMPLE_SIZE, random_state=42)
        sample_indices = sample_df.index.tolist()
        print(f"已随机选择 {len(sample_df)} 行进行评估。")

    # 3. 初始化文本处理器
    processor = TextProcess.TextProcessor()

    # 4. 遍历样本进行评估
    rows_to_process = [
        (index, row) for index, row in sample_df.iterrows() if index not in processed_indices
    ]
    
    with tqdm(total=len(sample_df), desc="评估进度") as pbar:
        pbar.update(len(processed_indices))
        
        for index, row in rows_to_process:
            eval_result, reason = None, None # 初始化变量
            doi = row.get('doi')
            if doi and isinstance(doi, str):
                doi = doi.split('_extracted_structured')[0]

            if not doi or pd.isna(doi):
                eval_result, reason = 'SKIPPED', '行缺少DOI。'
            else:
                pbar.set_description(f"处理 DOI: {doi[:20]}...")
                file_path = find_pdf_by_doi(doi, PDF_DIRECTORY)
                if not file_path:
                    eval_result, reason = 'FILE_NOT_FOUND', f"未能找到与DOI {doi} 对应的文件。"
                else:
                    try:
                        pdf_content = processor.read_json(file_path)
                        if not pdf_content:
                            eval_result, reason = 'PDF_READ_ERROR', f"文件 {file_path} 内容为空或读取失败。"
                        else:
                            # 去除doi字段，避免干扰评估
                            row_data = row.drop(labels=['doi'], errors='ignore')
                            # 转换为JSON字符串
                            row_data_json = row_data.to_json(indent=2, force_ascii=False)
                            eval_result, reason = evaluate_with_llm(pdf_content, row_data_json)
                    except Exception as e:
                        eval_result, reason = 'PROCESSING_ERROR', f"处理文件时发生未知错误: {e}"

            print(f"索引 {index} 的评估结果: {eval_result}, 原因: {reason}")
            # 修改 results 列表的结构
            results.append({'index': index, 'evaluation': eval_result, 'reason': reason})
            processed_indices.append(index)

            save_progress(processed_indices, results, sample_indices)
            pbar.update(1)

    # 5. 将评估结果合并回原始DataFrame
    if results:
        # 创建一个新的DataFrame来存储结果
        results_df = pd.DataFrame(results)
        results_df = results_df.set_index('index')
        results_df = results_df.rename(columns={'evaluation': 'evaluation_result', 'reason': 'evaluation_reason'})
        
        # 将新列合并到原始DataFrame
        df = df.join(results_df)
    
    # 6. 保存到新的CSV文件
    try:
        os.makedirs(os.path.dirname(OUTPUT_CSV_PATH), exist_ok=True)
        df.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8-sig')
        print(f"\n评估完成！结果已保存到: {OUTPUT_CSV_PATH}")

        if os.path.exists(PROGRESS_FILE_PATH):
            os.remove(PROGRESS_FILE_PATH)
            print(f"临时进度文件 {PROGRESS_FILE_PATH} 已被删除。")
    except Exception as e:
        print(f"保存结果到CSV时出错: {e}")

if __name__ == '__main__':
    main()