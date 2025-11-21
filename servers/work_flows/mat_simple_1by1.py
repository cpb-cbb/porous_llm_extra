import json
import logging
import re
from typing import Dict, Any, List, Optional
from servers.agents.manager import AgentFactory, AgentType
import json_repair
# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeneralLiteratureWorkflow:
    def __init__(self):
        # 初始化所有需要的通用 Agent
        self.pre_judge_agent = AgentFactory.get_agent(AgentType.GEN_PRE_JUDGE)
        self.process_agent = AgentFactory.get_agent(AgentType.GEN_PROCESS)
        self.micro_feature_agent = AgentFactory.get_agent(AgentType.GEN_MICRO_FEATURE)
        self.performance_agent = AgentFactory.get_agent(AgentType.GEN_PERFORMANCE)

    def process_document(self, doc_text: str) -> Dict[str, Any]:
        """
        处理单篇文献的完整流程
        """
        result = {
            "status": "failed",
            "samples": [],
            "data": {}
        }

        logger.info("Step 1: Pre-judging document...")
        # 1. 预判断与样本识别
        try:
            pre_judge_response = self.pre_judge_agent.run(doc_text)
            logger.info(f"Pre-judge response: {pre_judge_response}")
            
            if "不符合要求" in pre_judge_response:
                result["status"] = "skipped"
                result["reason"] = "Document not relevant"
                return result

            # 解析样本列表
            samples = json_repair.loads(pre_judge_response)
            
            if not samples:
                result["status"] = "skipped"
                result["reason"] = "No samples identified"
                return result

            result["samples"] = samples
            result["status"] = "processing"
            
        except Exception as e:
            logger.error(f"Error in pre-judge step: {e}")
            result["error"] = str(e)
            return result

        # 准备上下文输入 (通常是将样本列表和全文结合)
        context_input = f"Samples to extract: {samples}\n\nFull Text:\n{doc_text}"

        # 2. 提取实验过程
        logger.info("Step 2: Extracting experimental process...")
        raw_process_data = None
        try:
            raw_process_data = self.process_agent.run(context_input)
        except Exception as e:
            logger.error(f"Error in process extraction: {e}")

        # 3. 提取微观结构特征
        logger.info("Step 3: Extracting micro-features...")
        raw_micro_data = None
        try:
            raw_micro_data = self.micro_feature_agent.run(context_input)
        except Exception as e:
            logger.error(f"Error in micro-feature extraction: {e}")

        # 4. 提取性能指标
        logger.info("Step 4: Extracting performance metrics...")
        raw_perf_data = None
        try:
            raw_perf_data = self.performance_agent.run(context_input)
        except Exception as e:
            logger.error(f"Error in performance extraction: {e}")

        # 5. 整合数据：按样本归类
        logger.info("Step 5: Consolidating data by sample...")
        
        # 解析各个步骤的 JSON 响应
        process_dict = self._parse_json_response(raw_process_data)
        micro_dict = self._parse_json_response(raw_micro_data)
        perf_dict = self._parse_json_response(raw_perf_data)

        consolidated_data = {}
        for sample in samples:
            # 将每个样本的三个维度的信息整合到一个字典中
            # 注意：这里假设 Agent 返回的字典 key 就是样本名称
            consolidated_data[sample] = {
                "process": process_dict.get(sample),
                "micro_features": micro_dict.get(sample),
                "performance": perf_dict.get(sample)
            }
        
        result["data"] = consolidated_data
        result["status"] = "completed"
        return result

    def _parse_json_response(self, response: Optional[str]) -> Dict[str, Any]:
        """
        辅助函数：解析返回的 JSON 对象字符串
        """
        if not response:
            return {}
        try:
            # 寻找最外层的 {} 包裹的 JSON 内容
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
            return {}
        except Exception as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return {}

# 使用示例
if __name__ == "__main__":
    workflow = GeneralLiteratureWorkflow()
    
    # 模拟输入文本
    test_doc = """
    Abstract: We synthesized Sample-A using a hydrothermal method at 180C. 
    Results show it has a specific surface area of 1000 m2/g.
    """
    
    final_result = workflow.process_document(test_doc)
    print(json.dumps(final_result, indent=2, ensure_ascii=False))