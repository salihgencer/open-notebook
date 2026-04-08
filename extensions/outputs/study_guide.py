from extensions.outputs.base import BaseOutputGenerator


class StudyGuideGenerator(BaseOutputGenerator):
    name = "study_guide"
    title = "Study Guide"
    description = "Generates a structured study guide with key concepts, definitions, review questions, and summary."
    sections = ["overview", "key_concepts", "review_questions", "summary"]
    prompt_template = """You are a study guide generator. Create a comprehensive study guide from the following source material.

## Source Material
{context}

## Requirements
- Language: {language}
- Output format: Markdown
- Sections to include: {sections}

## Instructions
1. **Overview**: Brief introduction to the topic (2-3 sentences)
2. **Key Concepts**: List and explain each key concept with clear definitions
3. **Review Questions**: Generate 5-10 questions that test understanding of the material
4. **Summary**: Concise summary of the most important takeaways

Write clearly and concisely. Focus on the most important information from the sources."""
