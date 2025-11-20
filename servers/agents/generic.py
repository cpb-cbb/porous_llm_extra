# servers/agents/generic.py
from __future__ import annotations
from typing import Optional
from servers.agents.base import BaseLiteLLMAgent

class StandardExtractionAgent(BaseLiteLLMAgent):
    """
    通用的单输入提取 Agent。
    适用于只需要传入一段文本 (text_input) 并返回结果的场景。
    """
    def __init__(self, system_prompt: str, message_template: str = None, **kwargs) -> None:
        super().__init__(system_prompt=system_prompt, **kwargs)
        # 默认的 User 消息模板
        self.message_template = message_template or (
            "Original Text:\n```\n{text_input}\n```\n\n"
            "Please follow the requirements and output the extracted result:"
        )

    def build_messages(self, *, text_input: str) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": self.message_template.format(text_input=text_input),
            },
        ]

class BatchVerificationAgent(BaseLiteLLMAgent):
    """
    验证 Agent，保留其特殊的双参数逻辑。
    """
    def build_messages(self, *, text_input: str, answer: str) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": (
                    "the content need to be verified and corrected, Previous Answer:\n```\n{answer}\n```\n"
                    "Original Text:\n```\n{text_input}\n```"
                ).format(answer=answer, text_input=text_input),
            },
        ]