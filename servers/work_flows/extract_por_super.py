# 运行抽取 workflow
import shutil
from servers.agents.ele_chem_extract import ele_chem_extra
from servers.agents.pore_parameter_extract import micro_feature_extra
from servers.agents.proceess_extract import process_extra
from servers.agents.Validation_Agent import verifie_agent
from servers.agents.pre_judge import prejudge
from servers.utils import TextProcess
from servers.utils.tools import merge_agent_outputs_simple
import json
import os
import json_repair
processor = TextProcess.TextProcessor()
def loop_extract(agent_name, text_input, max_iter: int = 3):
    """
    如果 agent_name == "process_extraction"：
      - 调用 process_extra 获取初始答案；
      - 调用 verifie_agent 验证：
          * 若返回 "T" 则验证通过，返回当前答案；
          * 若返回修复后的 JSON 字符串，则将其作为新的答案继续验证；
      - 最多迭代 max_iter 次，超出返回最后一次结果。
      
    返回:
      tuple: (最终结果, 修改日志列表)
    """
    modification_log = []  # 记录所有修改
    
    if agent_name == "process_extraction":
        current_answer = process_extra(text_input)
    elif agent_name == "micro_feature_extraction":
        current_answer = micro_feature_extra(text_input)
    elif agent_name == "ele_chem_extraction":
        current_answer = ele_chem_extra(text_input)
    else:
        raise ValueError(f"未知的 agent_name: {agent_name}")
    
    if current_answer is None:
        modification_log.append({
            "iteration": 0,
            "status": "failed",
            "message": "初始提取失败，返回 None"
        })
        return None, modification_log
    
    # 记录初始提取结果
    modification_log.append({
        "iteration": 0,
        "status": "initial_extraction",
        "answer": current_answer,
        "message": f"agent_name: {agent_name} 初始提取成功"
    })
    
    print(f"agent_name: {agent_name}提取成功，开始验证...")
    
    for iteration in range(1, max_iter + 1):
        judge = verifie_agent(text_input=text_input, answer=current_answer)

        # 验证通过（约定返回 "T"）
        if isinstance(judge, str) and judge.strip() == "T":
            modification_log.append({
                "iteration": iteration,
                "status": "verified",
                "message": "验证通过",
                "final_answer": current_answer
            })
            print("验证通过，返回结果。")
            return json_repair.loads(current_answer), modification_log

        # 若返回为空或 None，则直接返回当前答案
        if not judge:
            modification_log.append({
                "iteration": iteration,
                "status": "empty_verification",
                "message": "验证返回为空，使用当前结果",
                "final_answer": current_answer
            })
            print("验证返回为空，返回当前结果。")
            return json_repair.loads(current_answer), modification_log

        # 否则认为 judge 为修复后的 JSON 字符串（或修正文本），将其作为下一轮的答案
        previous_answer = current_answer
        current_answer = judge
        
        modification_log.append({
            "iteration": iteration,
            "status": "modified",
            "message": "验证未通过，答案已修正",
            "previous_answer": previous_answer,
            "modified_answer": current_answer
        })
        
        print("验证未通过，继续迭代...,准备下一轮验证")
    
    # 达到最大迭代次数仍未通过，返回最后结果
    modification_log.append({
        "iteration": max_iter,
        "status": "max_iterations_reached",
        "message": f"达到最大迭代次数 {max_iter}",
        "final_answer": current_answer
    })
    
    print(f"达到最大迭代次数 {max_iter}，返回最后结果。")
    return json_repair.loads(current_answer), modification_log

def run_extraction_workflow(input_txt_path, output_json_path):
    unrelevant_dir = os.path.join(os.path.dirname(input_txt_path), "unrelevant")
    # 读取输入文本
    text_input = processor.read_json(input_txt_path) 
    print(f"读取输入文本，开始预判断...")
    # 预判断是否相关，及提取样本列表
    name_list_str = prejudge(text_input)
    name_dict=json_repair.loads(name_list_str)
    name_list = name_dict.get("samples", [])
    if not name_list:
        print("论文不相关，结束处理。")
        #将无关文件移到无关文件夹
        if not os.path.exists(unrelevant_dir):
            os.makedirs(unrelevant_dir)
        shutil.move(input_txt_path, os.path.join(unrelevant_dir, os.path.basename(input_txt_path)))
        return
    #输入文本应该为样本列表以及原文组成的字符串
    input_content = f"Sampleslist: {name_list}\n\nOriginal Text:\n{text_input}"
    
    # 初始化修改日志字典
    all_logs = {}
    
    # 1. 多孔炭工艺信息提取
    print(f"开始提取多孔炭工艺信息...")
    process_info, process_log = loop_extract("process_extraction", input_content)
    all_logs["process_extraction"] = process_log
    
    print(f"开始提取微观结构特征...")
    # 2. 微观结构特征提取
    micro_features, micro_log = loop_extract("micro_feature_extraction", input_content)
    all_logs["micro_feature_extraction"] = micro_log
    
    print(f"开始提取电化学性能提取...")
    # 3. 电化学性能提取
    ele_chem_info, ele_chem_log = loop_extract("ele_chem_extraction", input_content)
    all_logs["ele_chem_extraction"] = ele_chem_log
    
    # 4. 验证和整合结果
    final_result = merge_agent_outputs_simple(synthesis_data=process_info, properties_data=micro_features, performance_data=ele_chem_info, sample_list=name_list)

    result={
        "input_path": input_txt_path,
        "content": text_input,
        "process_info": process_info,
        "micro_features": micro_features,
        "ele_chem_info": ele_chem_info,
        "final_result": final_result,
        "modification_logs": all_logs  # 添加修改日志
    }
    # 保存结果到 JSON 文件
    import json
    with open(output_json_path, 'w', encoding='utf-8') as json_file:
        json.dump(result, json_file, ensure_ascii=False, indent=4)

    print(f"Extraction completed. Results saved to {output_json_path}")