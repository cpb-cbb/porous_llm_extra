# -*- coding: utf-8 -*-
import json
import os
import shutil
import time
from zhipuai import ZhipuAI
import json_repair
import multiprocessing
from functools import partial
from tqdm import tqdm
import traceback
from TextProcess import TextProcessor
# 处理文本的工具类 (Text processing utility class)
process = TextProcessor()
# --- Import Prompts ---
try:
    # 导入 CO2 捕集相关的提示词
    # Import prompts specific to CO2 capture
    import CO2_capture_carbon_prompts as prompts
except ImportError:
    print("错误：无法导入 CO2_capture_carbon_prompts.py。请确保该文件存在于同一目录中。")
    print("Error: Could not import CO2_capture_carbon_prompts.py. Please ensure it exists in the same directory.")
    exit()

# --- Configuration ---
# 从环境变量读取 API Key (Read API Key from environment variable)
api_key = os.environ.get('ZHIPUAI_API_KEY')
if not api_key:
    print("错误：未设置 ZHIPUAI_API_KEY 环境变量。")
    print("Error: ZHIPUAI_API_KEY environment variable not set.")
    exit()
client = ZhipuAI(api_key=api_key)

# API Call Configuration
# API 调用配置
MODEL_VERSION = "glm-4-air-250414" # 或者 "glm-4-air", "glm-4-airx" 等
API_RETRY_DELAY = 5 # seconds (API 调用重试延迟)
API_MAX_RETRIES = 3 # 最大重试次数

# --- Helper Functions ---

def parse_non_streaming_response(response):
    """解析非流式响应 (Parses non-streaming response)"""
    try:
        response_text = response.choices[0].message.content
        return response_text.strip()
    except (AttributeError, IndexError, TypeError) as e:
        print(f"解析响应时出错 (Error parsing response): {e}")
        print(f"原始响应 (Original response): {response}")
        return None

def zhipu_api_call(text_input, system_prompt, user_prompt, model=MODEL_VERSION, retries=API_MAX_RETRIES):
    """封装智谱 API 调用，包含重试逻辑 (Wraps ZhipuAI API call with retry logic)"""
    current_retry = 0
    while current_retry < retries:
        try:
            # 构建消息 (Construct messages)
            # 注意：CO2 提示词将主要指令放在 system_prompt 中
            # Note: CO2 prompts put the main instructions in the system_prompt
            messages = [
                {
                    "role": "system",
                    "content": system_prompt # 主要指令在这里 (Main instructions here)
                }
            ]
            # Step 1: text_input 是文献原文，user_prompt 通常为空或附加指令
            # Step 2: text_input 是 Step 1 的输出，user_prompt 通常为空
            # Step 1: text_input is the original literature, user_prompt is usually empty or for additional instructions
            # Step 2: text_input is the output of Step 1, user_prompt is usually empty
            if text_input: # 确保有输入内容 (Ensure there is input content)
                 messages.append({
                    "role": "user",
                    # 根据 system_prompt 的要求，user content 可能是原文或上一步结果
                    # Depending on the system_prompt, user content might be the original text or the previous step's result
                    "content": f"{user_prompt if user_prompt else ''}\n\nInput Text:\n```\n{text_input}\n```\n\nPlease follow the instructions in the system prompt."
                 })
            else:
                 print("警告：API 调用缺少输入文本。")
                 print("Warning: Missing input text for API call.")
                 return None # 没有输入文本，无法调用 (Cannot call without input text)


            response = client.chat.completions.create(
                model=model,
                messages=messages,
                top_p=0.7,
                temperature=0.1, # 较低的温度以确保精确提取 (Lower temperature for precise extraction)
                max_tokens=4000, # 根据需要调整 (Adjust as needed)
                stream=False
            )
            response_text = parse_non_streaming_response(response)
            if response_text:
                return response_text
            else:
                print(f"API 调用后解析响应失败，正在重试 ({current_retry + 1}/{retries})...")
                print(f"Response parsing failed after API call, retrying ({current_retry + 1}/{retries})...")

        except Exception as e:
            print(f"调用 ZhipuAI API 时出错 (Error calling ZhipuAI API): {e}")
            print(f"正在重试 ({current_retry + 1}/{retries})... (Retrying ({current_retry + 1}/{retries})...)")

        current_retry += 1
        time.sleep(API_RETRY_DELAY * (current_retry)) # 指数退避 (Exponential backoff)

    print(f"API 调用失败达到最大重试次数 ({retries})。")
    print(f"API call failed after maximum retries ({retries}).")
    return None

def extract_co2_info(txt, client, json_file, file_name, json_dir):
    """执行 CO2 信息提取和结构化 (Performs CO2 information extraction and structuring)"""
    intermediate_results = {}
    final_result = None

    # --- Step 1: Extract Semi-structured Information ---
    print("执行步骤 1: 提取半结构化信息 (CO2_CAP_1)...")
    print("Executing Step 1: Extracting Semi-structured Information (CO2_CAP_1)...")
    # 使用 PROMPT_CO2_CAP_1 作为 system prompt，原文作为 user content
    # Use PROMPT_CO2_CAP_1 as system prompt, original text as user content
    step1_output = zhipu_api_call(txt, prompts.PROMPT_CO2_CAP_1, None) # User prompt is empty
    intermediate_results['step_1_extraction_output'] = step1_output

    if not step1_output:
        print("步骤 1 失败或无响应。")
        print("Step 1 failed or no response.")
        final_result = {"error": "Extraction Step Failed or No Response"}
        return intermediate_results, final_result

    # 检查是否文献不相关 (Check if literature is irrelevant)
    if "该文献不符合要求" in step1_output:
        print("文献不符合要求，提取终止。")
        not_relevant_dir = os.path.join(json_dir, 'not_relevant')
        if not os.path.exists(not_relevant_dir):
            os.makedirs(not_relevant_dir)
            print(f"已创建不相关目录 (Created not relevant directory): {not_relevant_dir}")
        shutil.move(json_file, f'{not_relevant_dir}/{file_name}') # 移动文件到不相关目录 (Move file to not relevant directory)

        print("Literature does not meet requirements, stopping extraction.")
        final_result = {"status": "Not Relevant", "samples": []}
        # 将不相关信息也放入中间结果
        # Also put the irrelevant info into intermediate results
        intermediate_results['status'] = "Not Relevant"
        return intermediate_results, final_result

    # --- Step 2: Structure Data into JSON ---
    print("执行步骤 2: 数据结构化 (CO2_CAP_2)...")
    print("Executing Step 2: Data Structuring (CO2_CAP_2)...")
    # 使用 PROMPT_CO2_CAP_2 作为 system prompt，Step 1 的输出作为 user content
    # Use PROMPT_CO2_CAP_2 as system prompt, Step 1 output as user content
    step2_output_raw = zhipu_api_call(step1_output, prompts.PROMPT_CO2_CAP_2, None) # User prompt is empty
    intermediate_results['step_2_raw_output'] = step2_output_raw

    if step2_output_raw:
        print("尝试解析结构化 JSON...")
        print("Attempting to parse structured JSON...")
        try:
            # 使用 json_repair 修复可能的 JSON 格式问题 (Use json_repair to fix potential JSON format issues)
            final_result = json_repair.loads(step2_output_raw)
            print("JSON 解析成功。 (JSON parsing successful.)")
            # 验证是否为列表 (Validate if it's a list)
            if not isinstance(final_result, list):
                 print("警告：结构化输出不是预期的列表格式。")
                 print("Warning: Structured output is not in the expected list format.")
                 # 可以选择将其包装在列表中或标记为错误
                 # Optionally wrap it in a list or mark as error
                 final_result = {"error": "Structured output is not a list", "raw_output": step2_output_raw}

        except json_repair.JSONDecodeError as e:
            print(f"使用 json_repair 解析 JSON 时出错 (Error parsing JSON with json_repair): {e}")
            print(f"原始字符串输出 (Raw string output): {step2_output_raw}")
            final_result = {"error": "JSON Parsing Failed", "raw_output": step2_output_raw}
        except Exception as e: # 捕获其他可能的错误 (Catch other potential errors)
             print(f"解析 JSON 时发生意外错误 (Unexpected error parsing JSON): {e}")
             final_result = {"error": "Unexpected JSON Parsing Error", "raw_output": step2_output_raw}
    else:
        print("步骤 2 失败或无响应。 (Step 2 failed or no response.)")
        final_result = {"error": "Structuring Step Failed or No Response"}

    return intermediate_results, final_result

# --- Main Processing Logic ---

def process_file(file, json_dir, output_dir):
    """处理单个文件的函数，供多进程调用 (Processes a single file, for multiprocessing)"""
    file_name = os.path.splitext(file)[0]
    output_file = os.path.join(output_dir, f'{file_name}_co2_extracted.json')
    print(f"开始处理文件 (Starting processing for file): {file_name}")

    # 检查输出文件是否已存在（避免重复处理）(Check if output file exists to avoid reprocessing)
    if os.path.exists(output_file):
        print(f"跳过已处理文件 (Skipping already processed file): {file_name}")
        return f"跳过已处理文件: {file_name}"

    try:
        json_file=os.path.join(json_dir, file)
        json_data = process.read_json(json_file)
        if json_data == '非期刊数据':
            return f"{file} is not journal data"
        # 假设原始文本在 'query' 字段中 (Assuming original text is in 'query' field)
        # 或者根据你的 JSON 结构调整 (Or adjust based on your JSON structure)
        # txt = json_data.get("query") or json_data.get("text") or json_data.get("content")
        txt =json_data
        if not txt:
             print(f"文件 {file_name} 中缺少文本字段 ('query', 'text', or 'content')。")
             print(f"Text field ('query', 'text', or 'content') missing in file {file_name}.")
             return f"处理文件 {file_name} 时出错: 缺少文本字段"

        # 执行 CO2 信息提取 (Perform CO2 information extraction)
        intermediate_results, final_structured_result = extract_co2_info(txt, client,json_file,file_name,json_dir)

        # 准备最终输出的字典 (Prepare the final output dictionary)
        output_data = {
            'file_name': file_name,
            'original_text_snippet': txt, # 包含部分原文以便参考 (Include snippet for reference)
            'extraction_step_output': intermediate_results.get('step_1_extraction_output'), # Step 1 的输出 (Output of Step 1)
            'structuring_step_raw_output': intermediate_results.get('step_2_raw_output'), # Step 2 的原始输出 (Raw output of Step 2)
            'final_structured_result': final_structured_result, # 最终的结构化 JSON 或错误信息 (Final structured JSON or error info)
            'status': intermediate_results.get('status', 'Processed') # 添加处理状态 (Add processing status)
        }

        # 保存结果为 JSON 文件 (Save results as JSON file)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)

        status_msg = "成功处理" if output_data['status'] == 'Processed' else output_data['status']
        print(f"{status_msg}并保存文件 ({status_msg} and saved file): {file_name}")
        return f"{status_msg}: {file_name}"

    except json.JSONDecodeError as e:
        print(f"读取或解析输入 JSON 文件 {file} 时出错 (Error reading or parsing input JSON file {file}): {e}")
        return f"处理文件 {file} 时出错: 输入 JSON 无效"
    except Exception as e:
        print(f"处理文件 {file} 时发生意外错误 (Unexpected error processing file {file}): {e}")
        traceback.print_exc()
        return f"处理文件 {file} 时出错: {str(e)}"

def main(json_dir, output_dir, num_processes=4):
    """主函数，设置并运行多进程处理 (Main function to set up and run multiprocessing)"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"已创建输出目录 (Created output directory): {output_dir}")

    try:
        json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
        if not json_files:
             print(f"在目录 {json_dir} 中未找到 JSON 文件。")
             print(f"No JSON files found in directory {json_dir}.")
             return
        print(f"找到 {len(json_files)} 个 JSON 文件待处理。")
        print(f"Found {len(json_files)} JSON files to process.")
    except FileNotFoundError:
        print(f"错误：输入目录 {json_dir} 不存在。")
        print(f"Error: Input directory {json_dir} not found.")
        return
    except Exception as e:
        print(f"列出目录 {json_dir} 中的文件时出错 (Error listing files in directory {json_dir}): {e}")
        return

    print(f"使用 {num_processes} 个进程开始处理...")
    print(f"Starting processing with {num_processes} processes...")
    with multiprocessing.Pool(processes=num_processes) as pool:
        process_func = partial(process_file, json_dir=json_dir, output_dir=output_dir)
        results = list(tqdm(pool.imap_unordered(process_func, json_files), total=len(json_files), desc="处理文件 (Processing Files)"))

    # 显示处理结果摘要 (Display processing summary)
    skipped = sum(1 for r in results if r and r.startswith("跳过"))
    success = sum(1 for r in results if r and r.startswith("成功处理"))
    not_relevant = sum(1 for r in results if r and r.startswith("Not Relevant"))
    errors = sum(1 for r in results if r and r.startswith("处理文件") and "出错" in r)

    print(f"\n处理完成！ (Processing Complete!)")
    print(f"总文件数 (Total files): {len(json_files)}")
    print(f"成功处理 (Successfully processed): {success}")
    print(f"不相关 (Not Relevant): {not_relevant}")
    print(f"跳过处理 (Skipped): {skipped}")
    print(f"处理出错 (Errors): {errors}")
    if errors > 0:
        print("请检查日志或输出以获取错误详情。")
        print("Please check logs or output for error details.")

if __name__ == '__main__':
    # --- 配置输入输出路径 ---
    # --- Configure Input/Output Paths ---
    # !! 修改为你实际的路径 (!! CHANGE to your actual paths)
    # json_dir = '/Volumes/mac_outstore/work/cleaned_json' # 示例输入目录 (Example input directory)
    json_dir = '/Volumes/mac_outstore/毕业/jsol文献/biomass_co2_3000' # 例如: '/data/co2_papers_json' (e.g., '/data/co2_papers_json')
    # 输出目录将创建在输入目录下 (Output directory will be created inside the input directory)
    output_dir = os.path.join(json_dir, 'co2_extraction_output')

    # --- 配置进程数 ---
    # --- Configure Number of Processes ---
    print(f"检测到的 CPU 核心数 (Detected CPU cores): {os.cpu_count()}")
    num_processes = 4 # 根据 CPU 核心数和内存调整 (Adjust based on CPU cores and memory)
    # num_processes = os.cpu_count() // 2 # 或者使用一半的核心数 (Or use half the cores)

    # --- 运行主程序 ---
    if 'path/to/your' in json_dir:
         print("="*50)
         print("警告：请在运行前修改脚本中的 `json_dir` 变量为你包含 JSON 文件的实际目录路径！")
         print("WARNING: Please modify the `json_dir` variable in the script to your actual directory containing JSON files before running!")
         print("="*50)
    else:
        main(json_dir, output_dir, num_processes)
