# -*- coding: utf-8 -*-
import json
import os
import time # 引入 time 模块用于可能的延迟
from zai import ZhipuAI
import json_repair
import shutil
# 假设您已将之前的提示词保存为 prompts_script.py 文件
# Import prompts from the previously defined script
# Assuming the prompts are saved in 'prompts_script.py' in the same directory
try:
    import prompts_script
except ImportError:
    print("错误：无法导入 prompts_script.py。请确保该文件存在于同一目录中。")
    print("Error: Could not import prompts_script.py. Please ensure it exists in the same directory.")
    exit() # 如果无法导入提示词则退出

import multiprocessing
from functools import partial
from tqdm import tqdm
from TextProcess import TextProcessor
processor = TextProcessor()
# --- Configuration ---
# 从环境变量读取 API Key (Read API Key from environment variable)
api_key = os.environ.get('ZHIPUAI_API_KEY')
if not api_key:
    print("错误：未设置 ZHIPUAI_API_KEY 环境变量。")
    print("Error: ZHIPUAI_API_KEY environment variable not set.")
    exit()
client = ZhipuAI(api_key=api_key)

# System prompt for extraction steps (1.1 to 1.4)
# 提取步骤 (1.1 到 1.4) 的系统提示
system_extract = '''You are an assistant for extracting key information from literature. I need you to extract information from the literature according to the requirements.
                **Note**: If there are specific parameters, they must be extracted. Do not output vague statements.
                Respond with English only, no Chinese. Stick strictly to the output format requested in the prompt.'''

# System prompt for structuring step (2)
# 结构化步骤 (2) 的系统提示
system_structure = '''You are a database construction expert responsible for consolidating and structuring extracted material science data into a JSON format, following the provided schema precisely.
                Respond with the final JSON output only, without any additional text or explanations. Use null for missing data.'''

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
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                }
            ]
            # 如果 user_prompt 不为空，则添加用户消息 (Add user message if user_prompt is not empty)
            if user_prompt:
                 messages.append({
                    "role": "user",
                    "content": f"{user_prompt}\n\nOriginal Text:\n```\n{text_input}\n```\n\nPlease follow the requirements and output the extracted result:"
                 })
            # 如果 user_prompt 为空 (通常用于结构化步骤)，直接使用 text_input 作为用户内容
            # If user_prompt is empty (usually for structuring step), use text_input directly as user content
            else:
                 messages.append({
                    "role": "user",
                    "content": f"Please structure the following extracted information according to the schema provided in the system prompt:\n\nExtracted Information:\n```\n{text_input}\n```"
                 })

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                top_p=0.7,
                temperature=0.1,
                max_tokens=4000, # 根据需要调整 (Adjust as needed)
                # tools=[{"type": "web_search", "web_search": {"search_result": False}}], # 根据需要启用/禁用 (Enable/disable as needed)
                stream=False
            )
            response_text = parse_non_streaming_response(response)
            if response_text:
                return response_text
            else:
                # 解析失败也视为一种需要重试的情况 (Parsing failure is also considered a case for retry)
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


def extract_information_multi_step(txt, client,json_file, json_dir,file_name):
    """执行多步骤信息提取 (Performs multi-step information extraction)"""
    intermediate_results = {}
    final_result = None
    # --- Step 1.1: Relevance Check & Sample Identification ---
    print("执行步骤 1.1: 文献筛选与样本识别...")
    print("Executing Step 1.1: Document Relevance & Sample Identification...")
    step1_1_output = zhipu_api_call(txt, system_extract, prompts_script.prompt_1_1)
    intermediate_results['step_1_1_output'] = step1_1_output
    if "该文献不符合要求" in step1_1_output:
        print("文献不符合要求，提取终止。")
        not_relevant_dir = os.path.join(json_dir, 'not_relevant')
        if not os.path.exists(not_relevant_dir):
            os.makedirs(not_relevant_dir)
            print(f"已创建不相关目录 (Created not relevant directory): {not_relevant_dir}")
        shutil.move(json_file, f'{not_relevant_dir}/{json_file}') # 移动文件到不相关目录 (Move file to not relevant directory)
        final_result = {"status": "Not Relevant", "samples": []}
        return intermediate_results, final_result

    # --- Parse Sample List ---
    print("解析步骤 1.1 的样本列表...")
    print("Parsing sample list from Step 1.1...")
    sample_list = step1_1_output
    print(f"识别出的样本 (Identified samples): {sample_list}")
    # 将样本列表添加到用户提示中，供后续步骤使用 (Add sample list to user prompt for subsequent steps)
    sample_list_str = f"Identified Sample List: {json.dumps(sample_list)}"

    # --- Step 1.2: Synthesis Details ---
    print("执行步骤 1.2: 合成细节提取...")
    print("Executing Step 1.2: Synthesis Details Extraction...")
    prompt_1_2_with_samples = f"{prompts_script.prompt_1_2}\n\n{sample_list_str}"
    step1_2_output = zhipu_api_call(txt, system_extract, prompt_1_2_with_samples)
    intermediate_results['step_1_2_output'] = step1_2_output
    if not step1_2_output: print("步骤 1.2 失败或无响应。 (Step 1.2 failed or no response.)")

    # --- Step 1.3: Physical & Chemical Properties ---
    print("执行步骤 1.3: 物化性质提取...")
    print("Executing Step 1.3: Physical & Chemical Properties Extraction...")
    prompt_1_3_with_samples = f"{prompts_script.prompt_1_3}\n\n{sample_list_str}"
    step1_3_output = zhipu_api_call(txt, system_extract, prompt_1_3_with_samples)
    intermediate_results['step_1_3_output'] = step1_3_output
    if not step1_3_output: print("步骤 1.3 失败或无响应。 (Step 1.3 failed or no response.)")

    # --- Step 1.4: Electrochemical Performance ---
    print("执行步骤 1.4: 电化学性能提取...")
    print("Executing Step 1.4: Electrochemical Performance Extraction...")
    prompt_1_4_with_samples = f"{prompts_script.prompt_1_4}\n\n{sample_list_str}"
    step1_4_output = zhipu_api_call(txt, system_extract, prompt_1_4_with_samples)
    intermediate_results['step_1_4_output'] = step1_4_output
    if not step1_4_output: print("步骤 1.4 失败或无响应。 (Step 1.4 failed or no response.)")

    # --- Combine Intermediate Results for Structuring ---
    # 组合中间结果以进行结构化
    combined_extraction_text = f"""
    --- Synthesis Details (Step 1.2 Output) ---
    {step1_2_output if step1_2_output else "N/A"}

    --- Physical & Chemical Properties (Step 1.3 Output) ---
    {step1_3_output if step1_3_output else "N/A"}

    --- Electrochemical Performance (Step 1.4 Output) ---
    {step1_4_output if step1_4_output else "N/A"}

    --- Identified Sample List (from Step 1.1) ---
    {sample_list_str}
    """
    intermediate_results['combined_for_structuring'] = combined_extraction_text.strip()

    # --- Step 2: Data Structuring ---
    print("执行步骤 2: 数据结构化...")
    print("Executing Step 2: Data Structuring...")
    # 注意：这里我们将组合文本作为 "text_input" 传递，并将 user_prompt 设为 None 或空字符串
    # Note: Here we pass the combined text as "text_input" and set user_prompt to None or empty string
    step2_output_raw = zhipu_api_call(intermediate_results['combined_for_structuring'], prompts_script.prompt_2, None) # User prompt is empty
    intermediate_results['step_2_raw_output'] = step2_output_raw

    if step2_output_raw:
        print("尝试解析结构化 JSON...")
        print("Attempting to parse structured JSON...")
        try:
            # 使用 json_repair 修复可能的 JSON 格式问题 (Use json_repair to fix potential JSON format issues)
            final_result = json_repair.loads(step2_output_raw)
            print("JSON 解析成功。 (JSON parsing successful.)")
        except json_repair.JSONDecodeError as e:
            print(f"使用 json_repair 解析 JSON 时出错 (Error parsing JSON with json_repair): {e}")
            print("将存储原始字符串输出。 (Storing raw string output.)")
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
    output_file = os.path.join(output_dir, f'{file_name}_extracted_structured.json')
    print(f"开始处理文件 (Starting processing for file): {file_name}")

    # 检查输出文件是否已存在（避免重复处理）(Check if output file exists to avoid reprocessing)
    # if os.path.exists(output_file):
    #     print(f"跳过已处理文件 (Skipping already processed file): {file_name}")
    #     return f"跳过已处理文件: {file_name}"

    try:
        txt = processor.read_json(os.path.join(json_dir, file))
        if txt == '非期刊数据':
            return f"处理文件 {file} 时出错: 非期刊数据"
        # 执行多步骤提取 (Perform multi-step extraction)
        json_file = file
        intermediate_results, final_structured_result = extract_information_multi_step(txt, client,json_file, json_dir,file_name)

        # 准备最终输出的字典 (Prepare the final output dictionary)
        output_data = {
            'file_name': file_name,
            'original_text': txt,
            'intermediate_outputs': intermediate_results, # 包含所有中间步骤的输出 (Includes outputs from all intermediate steps)
            'structured_result': final_structured_result, # 最终的结构化 JSON 或错误信息 (Final structured JSON or error info)
            # 可以选择性地包含原始 JSON 中的其他信息 (Optionally include other info from original JSON)
            # 'original_llma8b_answer': json_data.get("response")
        }
        if final_structured_result:
            # 保存结果为 JSON 文件 (Save results as JSON file)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=4)

            print(f"成功处理并保存文件 (Successfully processed and saved file): {file_name}")
            return f"已处理: {file_name}"
        else:
            print(f"处理文件 {file_name} 时未生成有效的结构化结果 (No valid structured result generated for file {file_name})")
            return f"处理文件 {file} 时出错: 未生成有效的结构化结果"

    except json.JSONDecodeError as e:
        print(f"读取或解析输入 JSON 文件 {file} 时出错 (Error reading or parsing input JSON file {file}): {e}")
        return f"处理文件 {file} 时出错: 输入 JSON 无效"
    except Exception as e:
        print(f"处理文件 {file} 时发生意外错误 (Unexpected error processing file {file}): {e}")
        # 打印更详细的错误跟踪信息 (Print more detailed traceback)
        import traceback
        traceback.print_exc()
        return f"处理文件 {file} 时出错: {str(e)}"

def main(json_dir, output_dir, num_processes=4):
    """主函数，设置并运行多进程处理 (Main function to set up and run multiprocessing)"""
    # 确保输出目录存在 (Ensure output directory exists)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"已创建输出目录 (Created output directory): {output_dir}")

    # 获取所有 json 文件 (Get all json files)
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


    # 使用多进程处理文件 (Use multiprocessing to process files)
    print(f"使用 {num_processes} 个进程开始处理...")
    print(f"Starting processing with {num_processes} processes...")
    with multiprocessing.Pool(processes=num_processes) as pool:
        # 创建部分应用的函数，固定 json_dir 和 output_dir 参数
        # Create a partial function with fixed json_dir and output_dir arguments
        process_func = partial(process_file, json_dir=json_dir, output_dir=output_dir)

        # 使用 tqdm 显示进度 (Use tqdm to display progress)
        results = list(tqdm(pool.imap_unordered(process_func, json_files), total=len(json_files), desc="处理文件 (Processing Files)"))

    # 显示处理结果摘要 (Display processing summary)
    skipped = sum(1 for r in results if r and r.startswith("跳过"))
    success = sum(1 for r in results if r and r.startswith("已处理"))
    errors = sum(1 for r in results if r and r.startswith("处理文件") and "出错" in r)

    print(f"\n处理完成！ (Processing Complete!)")
    print(f"总文件数 (Total files): {len(json_files)}")
    print(f"成功处理 (Successfully processed): {success}")
    print(f"跳过处理 (Skipped): {skipped}")
    print(f"处理出错 (Errors): {errors}")
    if errors > 0:
        print("请检查日志或输出以获取错误详情。")
        print("Please check logs or output for error details.")

if __name__ == '__main__':
    # --- 配置输入输出路径 ---
    # --- Configure Input/Output Paths ---
    # !! 修改为你实际的路径 (!! CHANGE to your actual paths)
    # json_dir = '/Volumes/mac_outstore/work/cleaned_json'
    json_dir = '/Volumes/mac_outstore/毕业/jsol文献/biomass_super_2000' # 例如: '/data/papers_json' (e.g., '/data/papers_json')
    # 输出目录将创建在输入目录下 (Output directory will be created inside the input directory)
    output_dir = os.path.join(json_dir, 'multi_step_extraction_output')

    # --- 配置进程数 ---
    # --- Configure Number of Processes ---
    # 根据 CPU 核心数和内存调整 (Adjust based on CPU cores and memory)
    print(f"检测到的 CPU 核心数 (Detected CPU cores): {os.cpu_count()}") 
    num_processes = 4 # 例如: 设置为 4 (e.g., set to 4)
    # num_processes = os.cpu_count() // 2 # 或者使用一半的核心数 (Or use half the cores)

    # --- 运行主程序 ---
    # --- Run Main Program ---
    # 检查路径是否已修改 (Check if paths have been modified)
    if 'path/to/your' in json_dir:
         print("="*50)
         print("警告：请在运行前修改脚本中的 `json_dir` 变量为你包含 JSON 文件的实际目录路径！")
         print("WARNING: Please modify the `json_dir` variable in the script to your actual directory containing JSON files before running!")
         print("="*50)
    else:
        main(json_dir, output_dir, num_processes)
