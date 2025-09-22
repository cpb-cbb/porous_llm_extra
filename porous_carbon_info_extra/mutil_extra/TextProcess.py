import json
import os
import re

import fitz
import json_repair

class TextProcessor:
    """文本处理工具类"""
    
    @staticmethod
    def is_gibberish(text: str, threshold: int = 20) -> bool:
        """检查文本是否包含乱码"""
        vertical_tabs = re.findall(r'\v', text)
        return len(vertical_tabs) > threshold

    @staticmethod
    def read_text_file(file_path: str) -> str:
        """读取文本文件"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    @staticmethod
    def write_jsonl(data: dict, file_path: str) -> int:
        """写入JSONL文件并返回写入的字节数"""
        json_str = json.dumps(data, ensure_ascii=False)
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json_str + '\n')
        return len(json_str.encode('utf-8')) + 1
    @staticmethod
    def read_pdf( file_path: str) -> str:
        """读取PDF文件内容"""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            raise ValueError(f"PDF读取错误: {str(e)}")

    @staticmethod
    def read_json(file_path: str) -> str:
            """读取JSON文件内容"""
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data_type = data['full-text-retrieval-response']['coredata']['prism:aggregationType']
                if data_type != 'Journal':
                    return "非期刊数据"
                # 根据实际JSON结构调整提取逻辑
                if isinstance(data, str):
                    return data
                elif isinstance(data, dict):
                    full_text=data['full-text-retrieval-response']['originalText']
                    # 这里可以根据实际JSON结构自定义提取逻辑
                    text = json.dumps(full_text, ensure_ascii=False)
                elif isinstance(data, list):
                    return "\n".join(str(item) for item in data)
                else:
                    raise ValueError("不支持的JSON格式")
                # 删除参考文献部分与引言前的内容
                reference_index = text.rfind("References")
                introduction_index = text.find("Fig")
                if reference_index != -1:
                    # 找到了References部分
                    if introduction_index != -1 and introduction_index < reference_index:
                        # 如果找到了Introduction并且在References之前，截取中间部分
                        text = text[introduction_index:reference_index]
                    else:
                        # 如果没找到Introduction或Introduction在References之后，只截取References之前的部分
                        text = text[:reference_index]
                return text
            except Exception as e:
                raise ValueError(f"JSON读取错误: {str(e)}")
    
    @staticmethod
    def read_batchjsonl(file_path: str) -> str:
        """读取JSONL文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = f.readlines()
            return data
        except Exception as e:
            raise ValueError(f"JSONL读取错误: {str(e)}")
        
    @staticmethod
    def extract_assistant_content(jsonl_file_path: str) -> list:
        assistant_contents = []
        with open(jsonl_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                data = json.loads(line)
                response_body = data['response']['body']
                choices = response_body['choices']
                for choice in choices:
                    message = choice['message']
                    if message['role'] == 'assistant':
                        try:
                            content_dict = json_repair.loads(message['content'])
                            assistant_contents.append(content_dict)
                        except json.JSONDecodeError:
                            print(f"Failed to parse content: {message['content']}")
                            assistant_contents.append(message['content'])                  
        return assistant_contents
    
    @staticmethod
    def get_request_id(jsonl_file_path: str,txt_base_dir:str) -> list:
        file_names = []
        with open(jsonl_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                record = json.loads(line.strip())
                request_id=record['response']['body']['request_id']
                file_name = request_id.rsplit("-", 1)[0]
                txt_path = os.path.join(txt_base_dir, f"{file_name}")
                file_names.append(txt_path)
        return file_names
    @staticmethod
    def get_qwen_request_id(jsonl_file_path: str,txt_base_dir:str) -> list:
        file_names = []
        with open(jsonl_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                record = json.loads(line.strip())
                request_id=record['custom_id']
                file_name = request_id.rsplit("-", 1)[0]
                txt_path = os.path.join(txt_base_dir, f"{file_name}")
                file_names.append(txt_path)
        return file_names
        
    @staticmethod
    def extract_qwen_assistant_content(jsonl_file_path: str) -> list:
        assistant_contents = []
        with open(jsonl_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                data = json.loads(line)
                response_body = data['response']['body']
                choices = response_body['choices']
                for choice in choices:
                    message = choice['message']            
                    try:
                        content_dict = json_repair.loads(message['content'])
                        if content_dict is not None:
                            assistant_contents.append(content_dict)
                        else:
                            assistant_contents.append(message['content'])
                    except json.JSONDecodeError:
                        print(f"Failed to parse content: {message['content']}")
                        assistant_contents.append(message['content'])
        return assistant_contents