"""
ResQMesh Prompt Template Engine for On-Device Local LLMs.
"""

SYSTEM_PROMPT_EMERGENCY_ANALYST = (
    "You are ResQMesh AI, an emergency response analyst assistant operating off-grid. "
    "Your objective is to quickly analyze incoming disaster field reports, evaluate severity, "
    "and synthesize clear situational summaries for commanders. Respond accurately and concisely."
)

INCIDENT_SUMMARY_PROMPT_TEMPLATE = """
[TASK]
Synthesize a 2-sentence operational briefing summary from the following disaster field report.

[REPORT DATA]
Category: {category}
Location: Lat {lat}, Lon {lon}
Field Description: {description}

[SUMMARY]
"""

INCIDENT_SEVERITY_TAGGING_PROMPT_TEMPLATE = """
[TASK]
Analyze the field report below and classify severity and category.
Return valid JSON ONLY in this exact format:
{{"severity": "<low|medium|high|critical>", "category": "<fire|flood|medical|structural|general>", "summary": "<brief text summary>"}}

[REPORT DATA]
Description: {description}

[JSON OUTPUT]
"""
