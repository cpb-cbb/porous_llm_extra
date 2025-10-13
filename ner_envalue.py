# -*- coding: utf-8 -*-

from __future__ import annotations

from servers.agents.base import BaseZhipuAgent
from servers.utils import TextProcess
from servers.utils.prompts import NER_EVALUE_PROMPT_CN
import json
import os
import json_repair
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


def verifie_agent(*, text_input: str, answer: str | None):
    if answer is None:
        print("待验证内容为空，结束处理。")
        return None
    return _VERIFICATION_AGENT.run(text_input=text_input, answer=answer)
def count_total_facts(data):
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
                count += count_total_facts(value)
    elif isinstance(data, list):
        if not data:
            return 0
        for item in data:
            count += count_total_facts(item)
    # 过滤掉 None 和空字符串等无效叶节点
    elif data is not None and data != "":
        count = 1
    return count
# --- 新增函数 ---
def calculate_metrics(verification_list: list, total_ground_truth_facts: int) -> dict:
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
    # P (Population) is the total number of actual facts, which is `total_ground_truth_facts`
    tp_count = total_ground_truth_facts - fn_count

    # 计算精确率: TP / (TP + FP)
    # (TP + FP) 是所有提取出的结果数量
    if (tp_count + fp_count) > 0:
        precision = tp_count / (tp_count + fp_count)
    else:
        precision = 0.0

    # 计算召回率: TP / (TP + FN)
    # (TP + FN) 是所有应该被提取的真实结果数量，即 total_ground_truth_facts
    if total_ground_truth_facts > 0:
        recall = tp_count / total_ground_truth_facts
    else:
        recall = 0.0

    # 计算 F1 分数
    if (precision + recall) > 0:
        f1_score = 2 * (precision * recall) / (precision + recall)
    else:
        f1_score = 0.0

    return {
        "TP": tp_count,
        "FP": fp_count,
        "FN": fn_count,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4)
    }
# --- 新增函数结束 ---


if __name__ == "__main__":
   
   
   json_dir = "/Volumes/WD_work/test/test_out_vllm_1_size5"
   output_json_path = "record_evalue.json"

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
         if response is not None and isinstance(response, dict):
             answer = response["structured_output"]["investigated_systems"]
         else:
             answer = []
             print(f"文件 {json_file} 中 'response' 字段不是字典或为空，跳过处理。")
             continue

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
              total_facts = count_total_facts(answer)
              
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