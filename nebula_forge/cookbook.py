"""
NEBULA-FORGE — Skills Cookbook
Curated, high-quality example skills from PRDv2.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import SkillMetadata


@dataclass(frozen=True)
class SkillCookbookEntry:
    id: str
    name: str
    title: str
    category: str
    model_preference: str
    description: str
    tags: list[str]
    markdown: str

    def to_metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name=self.name,
            category=self.category,
            model_preference=self.model_preference,
            description=self.description,
            tags=self.tags,
            author="nebula-forge",
        )


COOKBOOK_ENTRIES: list[SkillCookbookEntry] = [
    SkillCookbookEntry(
        id="git-workflow",
        name="git-workflow",
        title="Git Workflow",
        category="workflow",
        model_preference="copilot/claude-sonnet-4-5",
        description="Use for commit messages, PR descriptions, conflict resolution, rebases, and branch strategy.",
        tags=["git", "commits", "pr", "workflow", "branching"],
        markdown="""---
name: git-workflow
category: workflow
version: 1.0.0
author: nebula-forge
model_preference: copilot/claude-sonnet-4-5
thinking_mode: auto
tags: git, commits, pr, workflow, branching
description: >
  Use for any git-related task: writing commit messages, creating PR descriptions,
  resolving merge conflicts, rebasing, and branch strategy design.
---

# Skill: git-workflow

## Purpose
Provide safe, high-signal git workflow guidance for day-to-day engineering tasks.

## When to Use This Skill
- Writing a commit message
- Drafting a PR description
- Resolving merge conflicts
- Planning branch naming and release flow

## Instructions
1. Infer task type (`commit`, `pr`, `conflict`, `branching`).
2. Ask for missing context only when required.
3. Prefer Conventional Commits for commit titles.
4. For conflicts: preserve both intents, explain resolution.
5. Always end with a concise actionable checklist.

## Output Format
Return sections in this order:
1. Summary
2. Proposed Output
3. Validation Checklist
4. Risks

## Examples
### Input
```text
write a commit message for adding JWT refresh rotation
```

### Output
```text
feat(auth): add JWT refresh token rotation

Implements sliding session windows using refresh token rotation.
Invalidates old refresh tokens to reduce replay risk.
```
""",
    ),
    SkillCookbookEntry(
        id="prompt-engineer",
        name="prompt-engineer",
        title="Prompt Engineer",
        category="ai",
        model_preference="copilot/claude-opus-4-6",
        description="Use when users want to improve, debug, or structure prompts for AI models.",
        tags=["prompting", "ai", "llm", "system-prompts", "few-shot"],
        markdown="""---
name: prompt-engineer
category: ai
version: 1.0.0
author: nebula-forge
model_preference: copilot/claude-opus-4-6
thinking_mode: auto
tags: prompting, ai, llm, system-prompts, few-shot
description: >
  Use when the user wants to write, improve, or debug prompts for AI models.
---

# Skill: prompt-engineer

## Purpose
Design prompts that are specific, testable, and aligned with desired output behavior.

## When to Use This Skill
- "Improve this prompt"
- "Why is the model hallucinating?"
- "Write a system prompt for this workflow"

## Instructions
1. Diagnose prompt gaps (role, task, context, constraints, output format).
2. Rewrite prompt with explicit structure.
3. Add few-shot examples when ambiguity is high.
4. Add guardrails (what to avoid, fallback behavior).
5. Explain why each change improves reliability.

## Output Format
Return sections: Diagnosis, Improved Prompt, Rationale, Optional Variants.

## Examples
### Input
```text
make this prompt better: explain this sql query
```

### Output
```text
Role: You are a senior database performance engineer.
Task: Explain what this SQL query does and where it may be slow.
Format: Problem, Query Walkthrough, Optimization Suggestions.
Constraints: Max 300 words. Do not invent schema fields.
```
""",
    ),
    SkillCookbookEntry(
        id="test-guardian",
        name="test-guardian",
        title="Test Guardian",
        category="testing",
        model_preference="copilot/gpt-5.1-codex-max",
        description="Use for writing robust tests, identifying coverage gaps, and designing failure-oriented test plans.",
        tags=["testing", "unit-tests", "integration", "qa", "reliability"],
        markdown="""---
name: test-guardian
category: testing
version: 1.0.0
author: nebula-forge
model_preference: copilot/gpt-5.1-codex-max
thinking_mode: auto
tags: testing, unit-tests, integration, qa, reliability
description: >
  Use for writing robust tests, identifying coverage gaps, and designing
  failure-oriented test plans.
---

# Skill: test-guardian

## Purpose
Increase confidence by creating tests for happy paths, edges, and failure modes.

## When to Use This Skill
- Add tests for new behavior
- Validate bug fixes with regression tests
- Improve confidence before refactors

## Instructions
1. Enumerate behavior matrix (happy/edge/error).
2. Prioritize deterministic tests.
3. Prefer boundary-focused assertions.
4. Add mocks at module boundaries only.
5. Explain what each test protects.

## Output Format
Return sections: Test Plan, Concrete Test Cases, Suggested File Layout, Risk Notes.

## Examples
### Input
```text
add tests for user registration service with duplicate email handling
```

### Output
```text
- should create user when email is new
- should reject duplicate email with explicit error code
- should rollback transaction when profile creation fails
```
""",
    ),
]


def search_cookbook(query: str) -> list[SkillCookbookEntry]:
    q = query.strip().lower()
    if not q:
        return list(COOKBOOK_ENTRIES)

    out: list[SkillCookbookEntry] = []
    for entry in COOKBOOK_ENTRIES:
        hay = " ".join([
            entry.id,
            entry.name,
            entry.title,
            entry.category,
            entry.description,
            ",".join(entry.tags),
        ]).lower()
        if q in hay:
            out.append(entry)
    return out
