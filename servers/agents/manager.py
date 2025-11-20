# servers/agents/manager.py
from __future__ import annotations
from enum import Enum
from typing import Any, Optional

from servers.agents.generic import StandardExtractionAgent, BatchVerificationAgent
from servers.utils.prompts_en import (
    prompt_1_1, # PreJudge
    prompt_1_2, # Process
    prompt_1_3, # Micro Feature
    prompt_1_4, # Electro Chemical
    prompt_batch_verifier_and_corrector
)
from core.config import settings

class AgentType(Enum):
    PRE_JUDGE = "pre_judge"
    PROCESS = "process"
    MICRO_FEATURE = "micro_feature"
    ELECTRO_CHEM = "electro_chem"
    VERIFIER = "verifier"

# 配置字典：定义每个 Agent 类型的 System Prompt 和 User Template
AGENT_CONFIG = {
    AgentType.PRE_JUDGE: {
        "class": StandardExtractionAgent,
        "system_prompt": prompt_1_1,
        "message_template": "Original Text:\n{text_input}" # PreJudge 特有的简单模板
    },
    AgentType.PROCESS: {
        "class": StandardExtractionAgent,
        "system_prompt": prompt_1_2,
        # 使用 StandardExtractionAgent 默认模板
    },
    AgentType.MICRO_FEATURE: {
        "class": StandardExtractionAgent,
        "system_prompt": prompt_1_3,
    },
    AgentType.ELECTRO_CHEM: {
        "class": StandardExtractionAgent,
        "system_prompt": prompt_1_4,
    },
    AgentType.VERIFIER: {
        "class": BatchVerificationAgent,
        "system_prompt": prompt_batch_verifier_and_corrector,
    }
}

class AgentFactory:
    _instances: dict[AgentType, Any] = {}

    @classmethod
    def get_agent(cls, agent_type: AgentType | str):
        """
        单例模式获取 Agent 实例。
        """
        if isinstance(agent_type, str):
            try:
                agent_type = AgentType(agent_type)
            except ValueError:
                raise ValueError(f"Unknown agent type: {agent_type}")

        if agent_type in cls._instances:
            return cls._instances[agent_type]

        config = AGENT_CONFIG.get(agent_type)
        if not config:
            raise ValueError(f"No configuration found for {agent_type}")

        agent_class = config["class"]
        
        # 实例化参数
        init_kwargs = {
            "system_prompt": config["system_prompt"],
            "model": settings.llm_model,
            "api_key": settings.llm_api_key,
            "temperature": settings.temperature,
            "top_p": settings.top_p,
            "max_tokens": settings.max_tokens,
        }
        
        # 添加 base_url (如果配置了的话)
        if settings.llm_base_url:
            init_kwargs["base_url"] = settings.llm_base_url
        
        if "message_template" in config:
            init_kwargs["message_template"] = config["message_template"]
        print(f"创建 Agent 实例: {agent_type.value} 使用模型 {settings.llm_model}")
        print(f"初始化参数信息: {init_kwargs}")    
        instance = agent_class(**init_kwargs)
        cls._instances[agent_type] = instance
        return instance

# 快捷调用入口
def run_agent(agent_type: str | AgentType, **kwargs):
    agent = AgentFactory.get_agent(agent_type)
    return agent.run(**kwargs)