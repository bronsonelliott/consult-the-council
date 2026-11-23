---
name: consult-the-council
description: Consult a council of external LLMs via OpenRouter to debate and critique plans before execution. Use when Claude Code creates a plan that would benefit from external review, when the user wants multiple AI perspectives on an approach, or when facing high-stakes decisions that warrant independent verification. Triggers on "/consult-the-council" command or requests for "council feedback", "multi-model review", or "LLM debate".
---

# Consult the Council

Query a panel of external LLMs via OpenRouter to debate, critique, and improve Claude Code's plans before execution.

## When to Use

- Before executing complex or high-stakes plans
- When the user explicitly requests council review
- When a plan has significant trade-offs worth external validation
- For architectural decisions, migrations, or breaking changes

## Quick Start

1. Get an OpenRouter API key at https://openrouter.ai/keys

2. Configure the key:
   ```bash
   cp config.env.template config.env
   # Edit config.env and paste your OPENROUTER_API_KEY
   ```

3. Run the council:
   ```bash
   python3 scripts/consult_council.py --plan "Your plan here"
   # Or from file:
   python3 scripts/consult_council.py --plan-file plan.md --output feedback.md
   ```

4. (Optional) Customize which models sit on the council by editing `council-models.md`.

## Council members

The council is whatever `council-models.md` (at the skill root) lists: one OpenRouter model ID per line, `#` comments ignored. Edit that file to change it, then run `--check-models` to confirm every ID exists. Full steps are in README.md under "Updating the models".

Browse available models at https://openrouter.ai/models. See `references/council-config.md` for model suggestions and API details.

## Workflow

1. **Prepare the plan** - Write a clear plan with context, steps, and expected outcomes
2. **Consult the council** - Run `consult_council.py` with the plan
3. **Review feedback** - Each member provides: Analysis, Strengths, Concerns, Recommendations, Verdict
4. **Synthesize consensus** - The report summarizes verdicts (APPROVE / APPROVE WITH CHANGES / REQUEST REVISION)
5. **Iterate if needed** - Revise plan based on feedback, re-consult if major changes

## Script Options

```
--plan TEXT        Plan text to review
--plan-file FILE   Read plan from file
--output FILE      Write report to file (default: council-feedback.md)
--sequential       Query models one at a time (default: parallel)
--json             Output raw JSON instead of formatted report
--timeout SECS     Timeout per model in seconds (default: 120)
--check-models     Check council-models.md IDs exist on OpenRouter, then exit (no key needed)
```

## Output Format

The council report includes:
1. **Plan Under Review** - The submitted plan
2. **Per-Member Feedback** - Each council member's analysis and verdict
3. **Council Summary** - Aggregated verdicts and consensus

## Error Handling

If a council member fails (API error, timeout, invalid model), the report shows the error while other members' feedback remains available. Missing API key is reported clearly with a link to get one.

## Configuration

One API key covers all models. Set `OPENROUTER_API_KEY` in `config.env`:

```bash
cp config.env.template config.env
```

Then edit `config.env`:
```
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

Get a key at: https://openrouter.ai/keys

**Important:** Never commit `config.env` to version control. Only `config.env.template` should be shared.

## Tips

- Provide sufficient context in plans (goals, constraints, alternatives considered)
- Use `--plan-file` for longer plans to avoid shell escaping issues
- Run `--sequential` for debugging API issues
- The council works best for substantive plans, not trivial tasks
