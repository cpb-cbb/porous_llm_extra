# -*- coding: utf-8 -*-

from __future__ import annotations

from servers.agents.base import BaseZhipuAgent
from servers.utils import TextProcess
from servers.utils.prompts_en import prompt_batch_verifier_and_corrector

processor = TextProcess.TextProcessor()


class BatchVerificationAgent(BaseZhipuAgent):
    def __init__(self) -> None:
        super().__init__(system_prompt=prompt_batch_verifier_and_corrector)#若要使用其他模型，传入 model 参数即可

    def build_messages(self, *, text_input: str, answer: str) -> list[dict[str, str]]:  # type: ignore[override]
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


_VERIFICATION_AGENT = BatchVerificationAgent()


def verifie_agent(*, text_input: str, answer: str | None):
    if answer is None:
        print("待验证内容为空，结束处理。")
        return None
    return _VERIFICATION_AGENT.run(text_input=text_input, answer=answer)


if __name__ == "__main__":
    pdf_path = "/Users/caopengbo/Downloads/1-s2.0-S0360544220323343-main.pdf"
    pdf_content = processor.read_pdf(pdf_path)
    extracted_info = verifie_agent(text_input=pdf_content, answer="{}")
    print(extracted_info)