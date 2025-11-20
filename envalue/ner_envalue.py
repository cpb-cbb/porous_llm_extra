# -*- coding: utf-8 -*-

from __future__ import annotations

from servers.agents.base import BaseZhipuAgent
from servers.utils import TextProcess
from servers.utils.prompts import NER_EVALUE_PROMPT_CN
import json
import os
import json_repair
import time
processor = TextProcess.TextProcessor()


class BatchVerificationAgent(BaseZhipuAgent):
    def __init__(self) -> None:
        super().__init__(system_prompt=NER_EVALUE_PROMPT_CN)#若要使用其他模型，传入 model 参数即可
  

    def build_messages(self, *, text_input: str, answer: str) -> list[dict[str, str]]:
        # 使用新的用户输入模板
        user_content = (
            "Please evaluate the following `Extracted JSON` based on the `Original Text` "
            "and provide the result strictly in the required JSON format.\n\n"
            "### Original Text:\n"
            "```\n{text_input}\n```\n\n"
            "### Extracted JSON:\n"
            "```json\n{answer}\n```"
        ).format(text_input=text_input, answer=answer)

        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_content},
        ]


_VERIFICATION_AGENT = BatchVerificationAgent()

def count_valid_items(item_list):
    """
    辅助函数：计算列表中有效的项目数量。
    一个项目被视为有效，当且仅当它是一个字典，并且同时包含 'name' 和 'value' 键，
    或者同时包含 'name' 和 'value_text' 键。
    """
    valid_count = 0
    number_valid_count = 0
    for item in item_list:
        # 确保我们处理的是一个字典
        if isinstance(item, dict):
            has_name = 'name' in item
            has_value = 'value' in item
            has_value_text = 'value_text' in item
            
            # 检查是否满足任一有效条件
            if (has_name and has_value) or (has_name and has_value_text):
                valid_count += 1
                # 一旦找到有效项，检查其value是否包含数字
                if has_value and any(c.isdigit() for c in str(item['value'])):
                    number_valid_count += 1
    return valid_count, number_valid_count

def count_total_facts_unified(data):
    """
    递归地计算数据中特定键的列表项总数，并对所有目标键中的项目进行统一的有效性验证。
    
    对于 'properties', 'system_characterization', 'performance_metrics'：
    只统计列表中同时包含 name/value 或 name/value_text 的项目。
    """
    # 定义需要统计列表长度的特定键
    LIST_COUNT_KEYS = {'properties', 'system_characterization', 'performance_metrics'}
    
    count = 0
    
    if isinstance(data, dict):
        for key, value in data.items():
            # 如果键是我们要找的特定键，并且其值是一个列表
            if key in LIST_COUNT_KEYS and isinstance(value, list):
                # 对所有目标键都使用统一的验证函数进行计数
                all_count, number_count = count_valid_items(value)
                count += number_count # 统计所有有效项目,若要统计含数字的项目，改为 number_count
            # 对于其他键，只要值是字典或列表，就继续递归探索
            elif isinstance(value, dict) or isinstance(value, list):
                count += count_total_facts_unified(value)
                
    elif isinstance(data, list):
        # 如果数据是列表，遍历列表中的每个元素并递归
        for item in data:
            count += count_total_facts_unified(item)
            
    return count
def verifie_agent(*, text_input: str, answer: str | None):
    if answer is None:
        print("待验证内容为空，结束处理。")
        return None
    return _VERIFICATION_AGENT.run(text_input=text_input, answer=answer)

def count_total_facts(data):
    """递归地计算数据中特定键的列表项总数。
    
    该函数仅统计 'properties', 'system_characterization', 'performance_metrics'
    这几个键对应的列表的长度。所有其他叶节点（如字符串、数字等）都将被忽略。
    """
    # 定义需要统计列表长度的特定键
    LIST_COUNT_KEYS = {'properties', 'system_characterization', 'performance_metrics'}
    
    count = 0
    
    if isinstance(data, dict):
        # 遍历字典的每一项
        for key, value in data.items():
            # 如果键是我们要找的特定键
            if key in LIST_COUNT_KEYS:
                # 并且其值是一个列表
                if isinstance(value, list):
                    # 直接累加列表的长度
                    count += len(value)
            # 对于其他键，我们不做任何处理，也不递归
            # 从而忽略了它们包含的所有内容

    elif isinstance(data, list):
        # 如果数据是列表，我们需要遍历列表中的每个元素
        # 因为目标字典可能嵌套在列表中
        for item in data:
            # 递归调用函数来处理列表中的每一项
            count += count_total_facts(item)
            
    # 注意：这里不再有 `elif data is not None...` 的判断，
    # 所以所有非字典/列表的叶节点都不会被计数。

    return count
def count_total_facts_corrected(data):
    """递归地计算数据中特定键的列表项总数。"""
    # 定义需要统计列表长度的特定键
    LIST_COUNT_KEYS = {'properties', 'system_characterization', 'performance_metrics'}
    
    count = 0
    
    if isinstance(data, dict):
        # 遍历字典的每一项
        for key, value in data.items():
            # 1. 首先，检查当前键是否是目标键，如果是，则累加其列表长度
            if key in LIST_COUNT_KEYS and isinstance(value, list):
                count += len(value)
            
            # 2. 然后，无论键是什么，只要值是字典或列表，就递归调用
            if isinstance(value, dict) or isinstance(value, list):
                count += count_total_facts_corrected(value)
                
    elif isinstance(data, list):
        # 如果数据是列表，遍历列表中的每个元素并递归
        for item in data:
            count += count_total_facts_corrected(item)
            
    return count
def count_totalsys_facts(data):
    """递归地计算数据中的事实总数(叶节点数量)
    
    对于特定键(properties, system_characterization, performance_metrics)
    直接统计列表长度,其他情况递归统计叶节点
    """
    # 定义需要统计列表长度的特定键
    LIST_COUNT_KEYS = {'properties', 'system_characterization', 'performance_metrics'}
    
    count = 0
    if isinstance(data, dict):
        if not data:
            return 0
        for key, value in data.items():
            # 如果是特定键且值是列表,直接统计列表长度
            if key in LIST_COUNT_KEYS and isinstance(value, list):
                count += len(value)
            else:
                count += count_totalsys_facts(value)
    elif isinstance(data, list):
        if not data:
            return 0
        for item in data:
            count += count_totalsys_facts(item)
    # 过滤掉 None 和空字符串等无效叶节点
    elif data is not None and data != "":
        count = 1
    return count
# --- 新增函数 ---
def calculate_metrics(verification_list: list, total_extracted_facts: int) -> dict:
    """
    根据验证结果计算精确率、召回率和F1分数。

    Args:
        verification_list: 从模型返回的包含FP和FN判断的列表。
        total_ground_truth_facts: 原始提取内容中的事实总数 (P)。

    Returns:
        一个包含TP, FP, FN, precision, recall, 和 f1_score 的字典。
    """
    if not isinstance(verification_list, list):
        print("警告: 验证结果不是一个列表，无法计算指标。")
        print(verification_list)
        return {
            "TP": 0, "FP": 0, "FN": 0,
            "precision": 0.0, "recall": 0.0, "f1_score": 0.0,
            "error": "Verification result was not a list."
        }
    
    fp_count = 0
    fn_count = 0
    for item in verification_list:
        judgment = item.get("Judgment", "").upper()
        if judgment == "FP":
            fp_count += 1
        elif judgment == "FN":
            fn_count += 1

    # 计算 TP (True Positives)
    # P = TP + FN  =>  TP = P - FN
    # P (Population) is the total number of actual facts, which is `total_extracted_facts`
    # 这里计算精确率，输入的 total_extracted_facts 应该是提取内容中的事实总数，并不是基准总数，而是抽取到的总数。所以总的总数应该为total_extracted_facts+
    tp_count = max(total_extracted_facts - fp_count, 0)

    # 计算精确率: TP / (TP + FP)
    # (TP + FP) 是所有提取出的结果数量
    if (tp_count + fp_count) > 0:
        precision = tp_count / (tp_count + fp_count)
    else:
        precision = 0.0

    # 计算召回率: TP / (TP + FN)
    # (TP + FN) 是所有应该被提取的真实结果数量，即 total_extracted_facts
    if total_extracted_facts > 0:
        recall = tp_count /(total_extracted_facts)
    else:
        recall = 0.0
    # 计算 F1 分数
    if (precision + recall) > 0:
        f1_score = 2 * (precision * recall) / (precision + recall)
    else:
        f1_score = 0.0

    return {
        "total_extracted_facts": total_extracted_facts,
        "TP": tp_count,
        "FP": fp_count,
        "FN": fn_count,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4)
    }
# --- 新增函数结束 ---


if __name__ == "__main__":

   
   json_dir = "/Volumes/WD_work/semi_parser-output_test"
   output_json_path = "/Volumes/WD_work/semi_parser-output_test-record-1027-11.json"

   processed_files = set()
   if os.path.exists(output_json_path) and os.path.getsize(output_json_path) > 0:
       try:
           with open(output_json_path, 'r', encoding='utf-8') as f:
               existing_data = json.load(f)
               if isinstance(existing_data, list):
                  for record in existing_data:
                      if isinstance(record, dict) and 'file_name' in record:
                          processed_files.add(record['file_name'])
       except (json.JSONDecodeError, Exception) as e:
           print(f"读取历史记录时发生错误，将重新开始: {e}")
   
   print(f"已找到 {len(processed_files)} 个已处理的文件记录。")

   json_files = [f for f in os.listdir(json_dir) if f.endswith(".json")]
   # 开始处理
   model_name = _VERIFICATION_AGENT.model
   print(f"使用模型: {model_name} 进行验证。")
   for json_file in json_files:
        
         if json_file in processed_files:
             print(f"文件 {json_file} 已处理过，跳过。")
             continue

         json_path = os.path.join(json_dir, json_file)
         try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
         except json.JSONDecodeError:
            print(f"文件 {json_file} 不是有效的JSON格式，跳过。")
            continue

         text_input = data.get("query", "")
         response = data.get("response", None)
         try:
            if response is not None and isinstance(response, dict):
                answer = response["structured_output"]["investigated_systems"]
                # total_facts = count_totalsys_facts(answer)
                # total_facts = count_total_facts_corrected(answer)
                total_facts = count_total_facts_unified(answer)
            else:
                answer = []
                print(f"文件 {json_file} 中 'response' 字段不是字典或为空，跳过处理。")
                continue
         except Exception as e:
              print(f"处理或保存文件 {json_file} 时出错: {e},可能为仿真类文献，无实验数据")

         if not text_input or answer is None:
              print(f"文件 {json_file} 中缺少 'query' 或 'response' 字段，跳过处理。")
              continue

         print(f"正在处理文件: {json_file}")
         verifie_result = verifie_agent(text_input=text_input, answer=json.dumps(answer, ensure_ascii=False))

         if verifie_result is None:
              print(f"文件 {json_file} 的验证结果为空，跳过保存。")
              continue
              
         try:
              repaired_json_str = json_repair.loads(verifie_result)

              # --- 修改部分 ---
              # 1. 计算原始提取文件中的事实总数
            #   total_facts = count_total_facts_corrected(answer)
            #   total_facts = count_total_facts_corrected(answer)
              total_facts = count_total_facts_unified(answer)
              # 2. 根据验证结果计算各项指标
              metrics = calculate_metrics(repaired_json_str, total_facts)
              
              # 3. 将文件名、指标和验证详情整合到结果中
              result_data = {
                "file_name": json_file,
                "metrics": metrics,
                "verification_details": repaired_json_str
              }
              # --- 修改结束 ---

              all_results = []
              if os.path.exists(output_json_path) and os.path.getsize(output_json_path) > 0:
                  try:
                      with open(output_json_path, 'r', encoding='utf-8') as f:
                          all_results = json.load(f)
                          if not isinstance(all_results, list):
                              all_results = []
                  except json.JSONDecodeError:
                      all_results = []
              
              all_results.append(result_data)

              with open(output_json_path, "w", encoding="utf-8") as out_f:
                json.dump(all_results, out_f, ensure_ascii=False, indent=4)
              
              print(f"验证结果及评估指标已追加到: {output_json_path}")

         except Exception as e:
              print(f"处理或保存文件 {json_file} 时出错: {e}")