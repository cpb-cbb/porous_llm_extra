import json
import pandas as pd
from openai import OpenAI
from collections import defaultdict
from core.config import settings
# 配置 OpenAI
client = OpenAI(api_key=settings.llm_api_key,base_url=settings.llm_base_url) # 替换你的 Key
print("✅ Gemini API 客户端已配置")

def flatten_json(y):
    """
    将嵌套的 JSON 展平为点分路径格式。
    例如: {"A": {"B": 1}} -> {"A.B": 1}
    """
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '.')
        elif type(x) is list:
            # 对于列表，简单处理为索引，或者根据具体需求调整
            for i, a in enumerate(x):
                flatten(a, name + str(i) + '.')
        else:
            out[name[:-1]] = x

    flatten(y)
    return out

def convert_sets_to_lists(obj):
    """
    递归地将对象中的所有 set 转换为 list，并处理其他不可序列化的类型
    
    Args:
        obj: 需要转换的对象
    
    Returns:
        转换后的对象
    """
    if isinstance(obj, dict):
        return {k: convert_sets_to_lists(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_sets_to_lists(item) for item in obj]
    elif isinstance(obj, set):
        return sorted(list(obj))  # 转换为排序的列表，保证一致性
    elif obj is ...:  # ellipsis 对象
        return "..."  # 转换为字符串
    elif obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    else:
        # 尝试转换为字符串
        try:
            return str(obj)
        except:
            return None

def get_agent_audit(source_text, flattened_json):
    """
    调用 Agent 进行审计，只返回问题条目。
    """
    # 转换 set 为 list，确保可以 JSON 序列化
    flattened_json = convert_sets_to_lists(flattened_json)
    
    # 将扁平化的 JSON 转为字符串，方便 Agent 阅读 Keys
    json_keys_str = json.dumps(flattened_json, indent=2, ensure_ascii=False)
    
    prompt = f"""
    你是一个严格的数据审计员。你的任务是校对“信息提取结果”与“原文”的一致性。
    
    输入数据：
    1. Flattened Extracted Data (Key-Value pairs): 提取出的数据。
    2. Source Text: 原始论文文本。

    规则：
    1. **默认假设提取是正确的**。你只需要报告**错误**或**遗漏**。
    2. 如果提取的值 (Extracted Value) 与原文 (Source Text) 明显冲突，标记为 "mismatch"。
    3. 如果提取的值为 null 或缺失，但原文中明确存在该数值，标记为 "missing"。
    4. 对于 "missing"，只关注重要的参数（如具体的数值、化学成分、电化学性能），忽略无关紧要的描述。
    5. 不要报告无关的废话，只输出 JSON。

    Source Text:
    \"\"\"{source_text}\"\"\"

    Flattened Extracted Data:
    \"\"\"{json_keys_str}\"\"\"

    请输出一个 JSON 列表，格式如下：
    [
        {{
            "key": "LPCM-600.Porosity.SpecificSurfaceArea_BET.value",
            "issue_type": "mismatch", 
            "extracted_value": 1600,
            "correct_value": 1621,
            "reason": "Table 1 shows 1621"
        }},
        {{
            "key": "LPCM-500.Porosity.SpecificSurfaceArea_BET.value",
            "issue_type": "missing",
            "extracted_value": null,
            "correct_value": 661.3,
            "reason": "Found in Table 1"
        }}
    ]
    如果完全没有错误，输出空列表 []。
    """

    response = client.chat.completions.create(
        model="gemini-2.5-pro", 
        messages=[{"role": "system", "content": "You are a QA auditor for data extraction. Output JSON only."}, 
                  {"role": "user", "content": prompt}],
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    
    # 解析返回的 JSON
    try:
        result = json.loads(response.choices[0].message.content)
        # 兼容处理，有时候 LLM 会把列表包在一个 key 里
        if isinstance(result, dict) and len(result) == 1:
            return list(result.values())[0]
        return result
    except:
        return []

def generate_evaluation_report_strict(extracted_json, agent_issues):
    """
    修正版：严格模式评估
    Mismatch (值不对) 会同时导致 FP+1 和 FN+1
    确保 TP + FN = Total Ground Truth
    """
    flat_data = flatten_json(extracted_json)
    
    # 建立问题索引
    issues_map = {item['key']: item for item in agent_issues}
    
    report_rows = []
    
    # 计数器
    tp_count = 0
    fp_count = 0 # 预测了但错了
    fn_count = 0 # 该有但没预测对
    tn_count = 0 # 都为空

    # 1. 遍历提取结果 (处理 TP, Mismatch, TN)
    # 注意：这里的 extracted_val 是预测值
    for key, extracted_val in flat_data.items():
        row = {
            "Key": key,
            "Extracted Value": extracted_val,
            "Ground Truth": extracted_val, # 初始假设一致
            "Status": "",
            "Reason": ""
        }
        
        is_extracted_empty = extracted_val is None or extracted_val == "null" or extracted_val == ""
        
        if key in issues_map:
            issue = issues_map[key]
            
            if issue['issue_type'] == 'mismatch':
                # 提取了值，但是错的
                # 判定：既是 FP (预测错值)，也是 FN (没拿到对值)
                row['Ground Truth'] = issue['correct_value']
                row['Status'] = "Mismatch" 
                row['Reason'] = issue['reason']
                
                fp_count += 1
                fn_count += 1 
                
            elif issue['issue_type'] == 'missing':
                # 这一步通常不会进入，因为 missing 一般意味着 extracted 是空的
                # 但如果 extracted 只有部分信息（如单位丢失），也可能走这里
                row['Ground Truth'] = issue['correct_value']
                row['Status'] = "FN"
                row['Reason'] = issue['reason']
                fn_count += 1
                
        else:
            # Agent 认为没问题
            if is_extracted_empty:
                # 预测空，Agent也认为该空 -> TN
                # 此时 GT 也是空
                row['Status'] = "TN"
                tn_count += 1
            else:
                # 预测有值，Agent认可 -> TP
                row['Status'] = "TP"
                tp_count += 1
        
        report_rows.append(row)

    # 2. 处理纯遗漏 (Agent 报了 missing，且 key 甚至可能不在 extracted 中)
    # 或者 key 在 extracted 中是 null，Agent 说它是 missing
    for issue in agent_issues:
        key = issue['key']
        # 如果这个 key 已经在上面处理过了（且被标记为 FN/Mismatch），就跳过
        # 如果上面没处理过（新key），或者上面处理的是 null 值（判定为 TN 但其实是 FN）
        
        # 简单起见，我们检查 report_rows 里有没有这个 key 且被正确标记
        existing_row = next((r for r in report_rows if r['Key'] == key), None)
        
        if not existing_row:
            # Key 完全不存在于提取结果中 -> 纯 FN
            row = {
                "Key": key,
                "Extracted Value": "NOT_EXIST",
                "Ground Truth": issue['correct_value'],
                "Status": "FN",
                "Reason": issue['reason']
            }
            report_rows.append(row)
            fn_count += 1
        elif existing_row['Status'] == 'TN' and issue['issue_type'] == 'missing':
            # 修正之前的 TN 判定为 FN
            existing_row['Status'] = "FN"
            existing_row['Ground Truth'] = issue['correct_value']
            existing_row['Reason'] = issue['reason']
            tn_count -= 1 # 撤销 TN
            fn_count += 1 # 增加 FN

    # 3. 生成 DataFrame
    df = pd.DataFrame(report_rows)
    
    # 4. 计算指标 (分母加微小值防止除零)
    
    # Precision = TP / (TP + FP)
    # 这里的 (TP + FP) 等于“模型给出的非空预测总数”
    precision = tp_count / (tp_count + fp_count + 1e-9)
    
    # Recall = TP / (TP + FN)
    # 这里的 (TP + FN) 等于“Ground Truth 中非空值的总数”
    recall = tp_count / (tp_count + fn_count + 1e-9)
    
    f1 = 2 * (precision * recall) / (precision + recall + 1e-9)

    # 验证守恒定律 (仅供调试打印)
    total_gt = tp_count + fn_count
    total_pred = tp_count + fp_count
    
    metrics = {
        "Precision": round(precision * 100, 2),
        "Recall": round(recall * 100, 2),
        "F1_Score": round(f1 * 100, 2),
        "TP": tp_count,
        "FP (Inaccurate Predictions)": fp_count,
        "FN (Missed Ground Truths)": fn_count,
        "TN (Correctly Empty)": tn_count,
        "Total Ground Truth Count": total_gt
    }

    return df, metrics

# ================= 使用示例 =================

if __name__ == "__main__":
    # 假设这是你的输入数据
    source_text = "..." # 填入你的原文
    extracted_data = {...} # 填入你的提取结果 JSON

    # 1. 扁平化数据供 Agent 参考
    flat_extracted = flatten_json(extracted_data)

    # 2. 运行 Agent (模拟输出，实际请取消上面 get_agent_audit 的注释并运行)
    # 假设 Agent 发现了两个问题：
    # LPCM-800 的比表面积提取错了（FP）
    # LPCM-500 的微孔体积漏了（FN）
    mock_agent_output = [
        {
            "key": "micro_features.LPCM-800.Porosity.SpecificSurfaceArea_BET.value",
            "issue_type": "mismatch",
            "extracted_value": 1852.2,
            "correct_value": 1852.5,
            "reason": "Text abstract says 1852.5, Table 1 says 1852.2. Minor inconsistency in paper."
        },
        {
            "key": "micro_features.LPCM-500.Porosity.MicroporeVolume.value",
            "issue_type": "missing",
            "extracted_value": None,
            "correct_value": 0.14,
            "reason": "Found in Table 1 row 2"
        }
    ]

    # 在实际使用中，取消下面这行的注释：
    agent_output = get_agent_audit(source_text, flat_extracted)
    # agent_output = mock_agent_output # 使用模拟数据演示

    # 3. 生成报告
    df_report, metrics = generate_evaluation_report_strict(extracted_data, agent_output)

    # 4. 输出结果
    print("=== 评估指标 ===")
    print(json.dumps(metrics, indent=2))

    print("\n=== 详细差异报告 (前5行) ===")
    print(df_report[df_report['Status'].isin(['FP', 'FN'])].head())

    # 5. 保存为 CSV
    df_report.to_csv("extraction_evaluation_report.csv", index=False)
    print("\n完整报告已保存至 extraction_evaluation_report.csv")