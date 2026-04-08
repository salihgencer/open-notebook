from extensions.outputs.base import BaseOutputGenerator


class TimelineGenerator(BaseOutputGenerator):
    name = "timeline"
    title = "Timeline"
    description = "Generates a chronological timeline of events, milestones, and developments."
    sections = ["events", "context"]
    prompt_template = """You are a timeline generator. Extract chronological events and milestones from the source material.

## Source Material
{context}

## Requirements
- Language: {language}
- Output format: Markdown
- Order events chronologically

## Instructions
1. Identify all dates, periods, and chronological references in the material
2. For each event, provide: date/period, event title, and brief context (1-2 sentences)
3. If exact dates aren't available, use relative ordering or approximate periods
4. Highlight key turning points or milestones

Format as:
### [Date/Period]
**[Event Title]**
[Brief context and significance]"""
