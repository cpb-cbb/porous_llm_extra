# -*- coding: utf-8 -*-

import os
import time # 引入 time 模块用于可能的延迟
from zai import ZhipuAiClient
from servers.utils import TextProcess
from servers.utils.prompts_en import prompt_1_1
processor = TextProcess.TextProcessor()
# --- Configuration ---
# 从环境变量读取 API Key (Read API Key from environment variable)
api_key = os.environ.get('ZHIPUAI_API_KEY')
if not api_key:
    print("错误：未设置 ZHIPUAI_API_KEY 环境变量。")
    print("Error: ZHIPUAI_API_KEY environment variable not set.")
    exit()
client = ZhipuAiClient(api_key=api_key)

# API Call Configuration
# API 调用配置
MODEL_VERSION = "glm-4.5" # 或者 "glm-4-air", "glm-4-airx" 等
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

def prejudge(text_input:str) -> str:
    """预先判断文献是否包含所需信息 (Pre-judge if the document contains required information)
    返回样本名称的列表，若不包含则返回 None (Returns a list of sample names, or None if not found)
    """
    current_retry = 0
    retries=API_MAX_RETRIES
    while current_retry < retries:
        try:
            # 构建消息 (Construct messages)
            messages=[
                {
                    "role": "system",
                    "content": prompt_1_1
                },
                {
                    "role": "user",
                    "content": f"Original Text:\n{text_input}"
                 }
            ]

            response = client.chat.completions.create(
                model=MODEL_VERSION,
                messages=messages,
                top_p=0.7,
                temperature=0.1,
                max_tokens=8000, # 根据需要调整 (Adjust as needed)
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


if __name__ == '__main__':
    # test_input = input('请输入问题')
    # answer=process_extra(test_input)
    # print(answer)
    pdf_path="/Users/caopengbo/Downloads/1-s2.0-S0360544220323343-main.pdf"
    pdf_content = processor.read_pdf(pdf_path)
    extracted_info = prejudge(pdf_content)
    print(extracted_info)