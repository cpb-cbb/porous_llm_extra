# -*- coding: utf-8 -*-

from __future__ import annotations

import json_repair

from servers.agents.base import BaseZhipuAgent
from servers.utils import TextProcess
from servers.utils.prompts_en import prompt_1_4

processor = TextProcess.TextProcessor()


class ElectroChemicalExtractionAgent(BaseZhipuAgent):
    def __init__(self) -> None:
        super().__init__(system_prompt=prompt_1_4)

    def build_messages(self, *, text_input: str) -> list[dict[str, str]]:  # type: ignore[override]
        return [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": (
                    "Original Text:\n```\n{text_input}\n```\n\nPlease follow the requirements and output the extracted result:"
                ).format(text_input=text_input),
            },
        ]

    def parse_response(self, content: str, **_: object):  # type: ignore[override]
        return content


_ELECTRO_AGENT = ElectroChemicalExtractionAgent()


def ele_chem_extra(text_input: str):
    return _ELECTRO_AGENT.run(text_input=text_input)


if __name__ == "__main__":
    pdf_path = "/Users/caopengbo/Downloads/1-s2.0-S0360544220323343-main.pdf"
    pdf_content = processor.read_pdf(pdf_path)
    extracted_info = ele_chem_extra(pdf_content)
    print(extracted_info)