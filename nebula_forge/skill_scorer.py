"""
NEBULA-FORGE — Skill Quality Scorer
Heuristic scoring for Skill Composer previews.
"""

from __future__ import annotations

import re

from .models import SkillQualityScore

CRITERIA = {
    "has_name": ("Add a skill name", 10),
    "has_description": ("Add a clear description", 15),
    "has_instructions": ("Add detailed instructions", 20),
    "has_examples": ("Add input/output examples", 15),
    "has_antipatterns": ("Add anti-patterns or constraints", 10),
    "has_output_format": ("Specify output format", 10),
    "has_tags": ("Add tags", 5),
    "has_model": ("Set model preference", 5),
    "substantial": ("Expand instructions to >200 words", 10),
}


def score_skill(frontmatter: dict[str, str], instructions: str, trigger: str, output_format: str) -> SkillQualityScore:
    criteria: dict[str, bool] = {}

    body = "\n".join([trigger or "", instructions or "", output_format or ""])

    criteria["has_name"] = bool((frontmatter.get("name") or "").strip())
    criteria["has_description"] = bool((frontmatter.get("description") or "").strip())
    criteria["has_tags"] = bool((frontmatter.get("tags") or "").strip())
    criteria["has_model"] = bool((frontmatter.get("model_preference") or "").strip())
    criteria["has_instructions"] = len((instructions or "").strip()) > 60
    criteria["has_examples"] = bool(re.search(r"example|input|output", body, flags=re.I))
    criteria["has_antipatterns"] = bool(re.search(r"anti-pattern|do not|never|avoid|constraint", body, flags=re.I))
    criteria["has_output_format"] = bool((output_format or "").strip())
    criteria["substantial"] = len((instructions or "").split()) > 200

    total = sum(points for key, (_, points) in CRITERIA.items() if criteria.get(key))
    suggestions = [label for key, (label, _) in CRITERIA.items() if not criteria.get(key)]

    return SkillQualityScore(total=total, criteria=criteria, suggestions=suggestions)
