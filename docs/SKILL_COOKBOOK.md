# Skills Cookbook

This cookbook contains production-style starter skills embedded into NEBULA-FORGE.

## In-App Access

1. Open Skill Factory (`F2`).
2. Select `Cookbook` tab.
3. Use:
   - `Load into Composer` to prefill the Composer form.
   - `Install Global` to write into global skill registry.
   - `Install Local` to write into current project's local skills path.

## Included Examples

## 1) Git Workflow (`git-workflow`)

Use when you need:

- Conventional commit messages
- Pull request summaries/checklists
- Merge conflict resolution structure

## 2) Prompt Engineer (`prompt-engineer`)

Use when you need:

- Prompt quality diagnostics
- Better system prompt structure
- Few-shot pattern generation

## 3) Test Guardian (`test-guardian`)

Use when you need:

- Test plans for feature changes
- Edge/error case coverage ideas
- Reliability-oriented test checklists

## How to Adapt a Cookbook Skill

1. Load into Composer.
2. Edit these first:
   - `Description`
   - `Trigger Description`
   - `Instructions`
   - `Output Format`
3. Refresh quality score.
4. Save as new skill name (`<team>-<purpose>`).
5. Publish through your team sync registry.

## Recommended Team Convention

- Prefix team skills with a domain (`backend-`, `frontend-`, `security-`, `ops-`).
- Require at least one input/output example.
- Pin `model_preference` explicitly.
- Keep `description` short and trigger-oriented.
