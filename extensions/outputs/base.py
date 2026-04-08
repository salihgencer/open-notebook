from abc import ABC
from typing import List


class BaseOutputGenerator(ABC):
    name: str = ""
    title: str = ""
    description: str = ""
    sections: List[str] = []
    prompt_template: str = ""

    def build_prompt(self, context: str, language: str = "en") -> str:
        return self.prompt_template.format(
            output_type=self.title,
            context=context,
            language=language,
            sections=", ".join(self.sections),
        )

    def format_output(self, raw_text: str) -> str:
        return raw_text
