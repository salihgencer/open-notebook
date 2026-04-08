from extensions.outputs.base import BaseOutputGenerator


class BriefingGenerator(BaseOutputGenerator):
    name = "briefing"
    title = "Briefing Document"
    description = "Generates an executive briefing with summary, key findings, and recommendations."
    sections = ["executive_summary", "key_findings", "recommendations", "next_steps"]
    prompt_template = """You are a briefing document generator. Create a professional executive briefing from the source material.

## Source Material
{context}

## Requirements
- Language: {language}
- Output format: Markdown
- Sections: {sections}
- Tone: Professional, concise, action-oriented

## Instructions
1. **Executive Summary**: 3-5 sentence overview of the most critical information
2. **Key Findings**: Bullet-pointed list of the most important facts and insights
3. **Recommendations**: Actionable recommendations based on the findings
4. **Next Steps**: Concrete next actions to take

Keep the briefing under 500 words. Prioritize actionable information over background details."""
