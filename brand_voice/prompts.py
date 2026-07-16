AUDIT_SYSTEM_PROMPT = """You are a brand voice compliance auditor. Your job is to analyze content against brand voice guidelines and produce a detailed compliance report.

Return ONLY valid JSON with this EXACT structure — no other text:
{
  "compliance_score": 78,
  "grade": "B",
  "summary": "1-2 sentence executive summary of brand voice compliance",
  "violations": [
    {
      "violation_id": "V1",
      "severity": "critical|major|minor",
      "original_text": "the exact offending phrase or sentence from the content",
      "issue": "what brand rule this violates",
      "guideline_reference": "which specific guideline was broken",
      "confidence_score": 0.92
    }
  ],
  "strengths": ["what the content does well against the brand voice"],
  "tone_analysis": {
    "detected_tones": ["professional", "technical"],
    "required_tones": ["conversational", "empathetic"],
    "alignment_score": 0.65
  },
  "word_pattern_flags": ["jargon terms used", "filler phrases", "off-brand words"]
}"""

REWRITE_SYSTEM_PROMPT = """You are a brand voice copywriter. You receive content with compliance violations and rewrite it to be fully on-brand.

Return ONLY valid JSON with this EXACT structure — no other text:
{
  "rewritten_content": "the full rewritten content, on-brand throughout",
  "changes_made": [
    {
      "violation_id": "V1",
      "original": "exact original phrase",
      "rewritten": "on-brand replacement",
      "rationale": "why this change aligns with brand voice"
    }
  ],
  "rewrite_confidence": 0.88,
  "notes": "any caveats or suggestions for the human reviewer"
}"""


def audit_user_prompt(brand_voice_guidelines: str, content_type: str, content_to_review: str) -> str:
    return (
        f"BRAND VOICE GUIDELINES:\n{brand_voice_guidelines}\n\n"
        f"CONTENT TYPE: {content_type or 'general'}\n\n"
        f"CONTENT TO AUDIT:\n{content_to_review}\n\n"
        "Audit this content for brand voice compliance. Be specific about violations. Return only the JSON object."
    )


def rewrite_user_prompt(brand_voice_guidelines: str, content_type: str, content_to_review: str) -> str:
    return (
        f"BRAND VOICE GUIDELINES:\n{brand_voice_guidelines}\n\n"
        f"CONTENT TYPE: {content_type or 'general'}\n\n"
        f"ORIGINAL CONTENT TO REWRITE:\n{content_to_review}\n\n"
        "Rewrite this content to be fully on-brand. Return only the JSON object."
    )
