from extensions.outputs.base import BaseOutputGenerator


class FAQGenerator(BaseOutputGenerator):
    name = "faq"
    title = "FAQ"
    description = "Generates frequently asked questions and answers based on source material."
    sections = ["questions_and_answers"]
    prompt_template = """You are a FAQ generator. Extract the most important questions and provide clear answers from the source material.

## Source Material
{context}

## Requirements
- Language: {language}
- Output format: Markdown
- Generate 8-15 question-answer pairs

## Instructions
1. Identify the key topics and common questions someone would ask about this material
2. Write each question as someone unfamiliar with the topic would ask it
3. Provide clear, concise answers grounded in the source material
4. Order questions from most fundamental to most specific

Format each Q&A as:
### Q: [Question]
**A:** [Answer]"""
