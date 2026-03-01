from nebula_forge.skill_scorer import score_skill


def test_score_skill_basics():
    frontmatter = {
        "name": "code-reviewer",
        "description": "Review code quality and safety",
        "tags": "review,security",
        "model_preference": "copilot/claude-opus-4-6",
        "category": "code-review",
    }
    score = score_skill(
        frontmatter,
        instructions="Analyze diff and return prioritized issues with rationale.",
        trigger="Use when user asks for code review.",
        output_format="Summary, Findings, Risks",
    )

    assert score.total > 0
    assert score.criteria["has_name"] is True
    assert score.criteria["has_model"] is True
    assert score.criteria["has_output_format"] is True


def test_score_skill_suggests_missing_items():
    score = score_skill(
        {"name": "", "description": "", "tags": "", "model_preference": ""},
        instructions="short",
        trigger="",
        output_format="",
    )

    assert score.total < 30
    assert any("skill name" in s.lower() for s in score.suggestions)
    assert any("description" in s.lower() for s in score.suggestions)
