import json
import re
import os
import json_repair
from openai import OpenAI
from tqdm import tqdm
import multiprocessing
from functools import partial
import sys
from prompt import PROMPT1,PROMPT2
# 可选的PDF处理
try:
    import fitz  # PyMuPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
sys.path.append('/Users/caopengbo/Documents/BATCH code')
from porous_carbon_info_extra.qwen_batch.TextProcess import TextProcessor
process = TextProcessor()

def read_file(file_path):
    """根据文件类型读取内容"""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    elif file_ext == '.json':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'text' in data:
                return data['text']
            return json.dumps(data, ensure_ascii=False)
    elif file_ext == '.pdf':
        if not PDF_SUPPORT:
            raise ImportError("处理PDF需要安装PyMuPDF: pip install pymupdf")
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    else:
        raise ValueError(f"不支持的文件类型: {file_ext}")
def deepseek_chat(prompt, txt, model="deepseek-reasoner"):
    client = OpenAI(api_key="sk-7f581df2297441b8aca5e4c731e3462a", base_url="https://api.deepseek.com")

    response = client.chat.completions.create(
        model=model,  # 'deepseek-reasoner'
        messages=[
            {"role": "user", "content": f"{prompt}\nhere are the artical need t p be extrated:{txt}"},
        ],
        temperature=1,
        stream=False
    )
    return response.choices[0].message.content
def zhipuai_chat(prompt, txt, model="glm-4-airx"):
    client = OpenAI(
        api_key="734c7160f2f74b9ab46c69b6823eefe2.eKeeXrVDR0B5K02A",
        base_url="https://open.bigmodel.cn/api/paas/v4/"
    ) 

    response = client.chat.completions.create(
        model=model,  
        messages=[
            {"role": "user", "content": f"{prompt}\nhere are the artical need t p be extrated:{txt}"},
        ],
        top_p=0.7,  
        temperature=0.1,
        max_tokens=4000,
    ) 
    return response.choices[0].message.content

def get_all_txt_files(directory):
    """获取目录及其子目录中的所有txt文件"""
    all_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt'):
                all_files.append(os.path.join(root, file))
    return all_files

def process_file(file_path, outputdir, prompt):
    try:
        # 获取文件名并构建输出文件路径
        filename = os.path.basename(file_path)
        name = os.path.splitext(filename)[0]
        # output_file = os.path.join(outputdir, f"{os.path.splitext(filename)[0]}.json")
        output_file = os.path.join(outputdir, name + ".json")

        # # 检查输出文件是否已存在（避免重复处理）
        if os.path.exists(output_file):
            return f"跳过已处理文件: {filename}"
        ## 读取文本文件内容

        # 读取json文件内容(originally was txt)
        text = process.read_json(file_path)
        if text == "非期刊数据":
            return f"跳过空文件: {filename}"
        # 读取 json 中的某个键

        # 调用 API 处理文本
        deep_response = deepseek_chat(PROMPT1, text)
        api_response = zhipuai_chat(PROMPT2, deep_response)
        try:
            # 尝试解析为JSON
            parsed_response = json_repair.loads(api_response)
            ##直接保存原始响应
            # parsed_response = api_response
        except Exception:
            # 如果无法解析为JSON，则保存原始响应
            parsed_response = api_response
            
        answer = {"original_text": text,"key_info":deep_response,"answer": parsed_response}
        
        # 保存回答为json文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(answer, f, ensure_ascii=False, indent=4)
        
        return f"已保存: {output_file}"
    except Exception as e:
        return f"处理错误 {file_path}: {str(e)}"

def main(txt_dir, outputdir, prompt, num_processes=4):
    # 获取所有txt文件
    # txt_files = get_all_txt_files(txt_dir)
    # print(f"找到 {len(txt_files)} 个txt文件")
    
    # 按修改时间排序
    # txt_files.sort(key=lambda fn: -os.path.getmtime(fn))
    
    # 获取所有json文件
    txt_files = [f for f in os.listdir(txt_dir) if f.endswith('.json')]
    txt_file_paths = [os.path.join(txt_dir, f) for f in txt_files]

    # 确保输出目录存在
    os.makedirs(outputdir, exist_ok=True)
    
    # 使用多进程处理文件
    with multiprocessing.Pool(processes=num_processes) as pool:
        # 创建部分应用的函数，固定outputdir和prompt参数
        process_func = partial(process_file, outputdir=outputdir, prompt=prompt)
        
        # 使用tqdm显示进度
        results = list(tqdm(pool.imap(process_func, txt_file_paths), total=len(txt_files), desc="处理文件"))
    
    # 显示处理结果摘要
    skipped = sum(1 for r in results if r.startswith("跳过"))
    success = sum(1 for r in results if r.startswith("已保存"))
    errors = sum(1 for r in results if r.startswith("处理错误"))
    
    print(f"\n处理完成！总文件数: {len(txt_file_paths)}, 成功: {success}, 跳过: {skipped}, 错误: {errors}")

if __name__ == '__main__':
    # txt_dir = "/Volumes/mac_outstore/work/高含量数据/抽样数据集/txt"
    input_dir = "/Volumes/mac_outstore/毕业/jsol文献/biomass_super_2000"
    outputdir = "/Volumes/mac_outstore/毕业/answer/bio-2000"
    os.makedirs(outputdir, exist_ok=True)
    
    with open('steel_extra/prompt-steel.txt', 'r', encoding='utf-8') as f:
        prompt = f.read()
    # 可配置的进程数，根据CPU核心数和任务性质调整
    num_processes = 2 # 可以根据您的系统调整此值
    main(input_dir, outputdir, prompt, num_processes)