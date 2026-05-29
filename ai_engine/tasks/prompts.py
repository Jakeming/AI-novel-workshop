"""
prompts.py — Prompt templates for each AI task.

Registered with LLM client via @register_prompt decorator.
Each fn receives ctx dict, returns prompt string.
"""
from ai_engine.core.llm import register_prompt


@register_prompt("deep_read")
def deep_read_prompt(ctx: dict) -> str:
    return f"""You are an expert literary analyst. Perform a deep reading of the following text.

Stage: {ctx.get("stage", "novice")}
Text: {ctx.get("original_text", "")}

Output JSON with:
- summary (<=150 chars)
- emotion_curve: array of {{position (char offset), valence (-1 to 1), arousal (0 to 1)}}, one entry per ~200 words
- hooks: array of {{position, type}} where type is one of: 悬念/冲突爆发/情感冲击/反转
- paragraph_functions: array of {{start (char offset), end, function}} where function is one of: 背景/冲突引入/发展/高潮/过渡/闭环"""


@register_prompt("deconstruct")
def deconstruct_prompt(ctx: dict) -> str:
    return f"""You are an expert literary analyst. Perform a layered deconstruction.

Text: {ctx.get("original_text", "")}

Output JSON with:
- intent: abstract description of the core message/intent
- structure: "起承转合" description
- plot: array of key plot points (strings)
- language: sentence patterns, rhetorical devices used
- portable_logic: array of narrative patterns reusable across genres (extract only high-frequency patterns, NOT specific plot elements)
- specific_elements: array of passages containing concrete names, places, events (NOT reusable)"""


@register_prompt("map_skeleton")
def skeleton_prompt(ctx: dict) -> str:
    return f"""You are an expert narrative analyst. Map the following story to an abstract narrative skeleton.

Original text: {ctx.get("original_text", "")}
User's three answers:
- Conflict cause: {ctx.get("user_answers", {}).get("conflict_cause", "")}
- Motivation: {ctx.get("user_answers", {}).get("motivation", "")}
- Value core: {ctx.get("user_answers", {}).get("value_core", "")}

Output JSON with:
- text_skeleton: trigger -> conflict1 -> ... -> resolution (abstract, no specific names)
- mermaid_code: valid Mermaid graph TD syntax describing the skeleton"""


@register_prompt("strip_test")
def strip_test_prompt(ctx: dict) -> str:
    import random
    GENRES = ["科幻", "职场", "校园", "家庭伦理", "奇幻", "侦探", "医疗", "体育", "宫廷", "末日"]
    chosen = random.sample(GENRES, 3)
    specific = ctx.get("specific_element", "")
    return f"""Rewrite the following passage into {chosen[0]}, {chosen[1]}, and {chosen[2]} settings.
Keep: sentence structure, emotional rhythm, rhetorical devices.
Change: all concrete nouns, verbs, characters, items to match the target genre.
Each version ≤100 characters.

Original: {specific}

Output JSON with:
- original: the original passage
- test_cases: array of {{genre, rewritten}}"""


@register_prompt("prompt_self_reflection")
def reflection_prompt(ctx: dict) -> str:
    return f"""The user's imitation draft has failed similarity validation.
Dimensions:
- Conflict similarity: {ctx.get("conflict_similarity", "?")}
- Motivation similarity: {ctx.get("motivation_similarity", "?")}
- Value similarity: {ctx.get("value_similarity", "?")}
- Warnings: {ctx.get("warnings", [])}

Generate 3 Socratic questions that help the user find their own path to differentiation.
Do NOT suggest specific changes. Questions should probe: conflict cause, character motivation, value core.

Output JSON with:
- questions: array of 3 strings"""


@register_prompt("narrative_consistency_check")
def consistency_prompt(ctx: dict) -> str:
    return f"""Check the following imitation text for internal consistency issues.

Text: {ctx.get("imitation_text", "")}

Output JSON with:
- inconsistencies: array of {{type: "critical"|"advisory", description: string}}
  critical: character name changes, logical contradictions, plot holes
  advisory: tonal shifts, style inconsistencies, minor timeline issues"""
