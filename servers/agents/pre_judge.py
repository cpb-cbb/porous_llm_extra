# -*- coding: utf-8 -*-

from __future__ import annotations

from servers.agents.base import BaseZhipuAgent
from servers.utils import TextProcess
from servers.utils.prompts_en import prompt_1_1

processor = TextProcess.TextProcessor()


class PreJudgeAgent(BaseZhipuAgent):
    def __init__(self) -> None:
        super().__init__(system_prompt=prompt_1_1)

    def build_messages(self, *, text_input: str) -> list[dict[str, str]]:  # type: ignore[override]
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Original Text:\n{text_input}"},
        ]


_PRE_JUDGE_AGENT = PreJudgeAgent()


def prejudge(text_input: str):
    return _PRE_JUDGE_AGENT.run(text_input=text_input)


if __name__ == "__main__":
    pdf_path = "/Users/caopengbo/Downloads/1-s2.0-S0360544220323343-main.pdf"
    pdf_content = processor.read_pdf(pdf_path)
    extracted_info = prejudge(pdf_content)
    print(extracted_info)