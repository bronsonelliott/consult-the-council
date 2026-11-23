#!/usr/bin/env python3
"""
Consult the Council - Query multiple LLMs via OpenRouter for plan debate and feedback.

Usage:
    python consult_council.py --plan "Your plan text here"
    python consult_council.py --plan-file plan.md
    python consult_council.py --plan "Plan text" --output council-feedback.md

API key can be provided via:
    1. config.env file in the skill directory (copy from config.env.template)
    2. Environment variable: OPENROUTER_API_KEY
"""

import argparse
import json
import os
from pathlib import Path
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request
import urllib.error


SKILL_DIR = Path(__file__).resolve().parent.parent

# Used only when council-models.md is missing or has no valid model IDs.
# To change the council, edit council-models.md instead of this list.
DEFAULT_MODELS = [
    "openai/gpt-6.2-astra-pro",
    "google/gemini-4-neon",
    "moonshotai/kimi-k3.1-pro",
]

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

DEBATE_SYSTEM_PROMPT = """You are a member of a council of AI experts reviewing a plan. Your role is to:

1. ANALYZE the plan critically but constructively
2. IDENTIFY potential weaknesses, risks, or blind spots
3. SUGGEST specific improvements or alternatives
4. HIGHLIGHT what's strong about the plan
5. PROVIDE a clear verdict: APPROVE, APPROVE WITH CHANGES, or REQUEST REVISION

Be direct, specific, and actionable. Avoid generic feedback.

Format your response as:
## Analysis
[Your critical analysis]

## Strengths
[What works well]

## Concerns
[Specific issues or risks]

## Recommendations
[Concrete suggestions]

## Verdict
[APPROVE / APPROVE WITH CHANGES / REQUEST REVISION] - [Brief rationale]"""

KNOWN_VERDICTS = ("APPROVE WITH CHANGES", "REQUEST REVISION", "APPROVE")


def load_config():
    """Load API keys from config.env file if it exists."""
    config_path = SKILL_DIR / "config.env"

    if config_path.exists():
        with open(config_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if value:  # Only set if value is non-empty
                        os.environ[key] = value


def load_council_models() -> list[str]:
    """Load council model IDs from council-models.md. Falls back to defaults if missing."""
    models_path = SKILL_DIR / "council-models.md"

    model_ids = []
    if models_path.exists():
        with open(models_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Validate provider/model format
                if re.match(r"^[\w.-]+/[\w.:+-]+$", line):
                    model_ids.append(line)

    return model_ids or DEFAULT_MODELS


def get_api_key() -> str:
    """Get OpenRouter API key from environment."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise ValueError(
            "Missing OPENROUTER_API_KEY. "
            "Set it in config.env or as an environment variable. "
            "Get a key at: https://openrouter.ai/keys"
        )
    return key


def query_openrouter(model_id: str, plan: str, timeout: int = 120) -> str:
    """Query a model via OpenRouter's OpenAI-compatible API."""
    api_key = get_api_key()

    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": DEBATE_SYSTEM_PROMPT},
            {"role": "user", "content": f"Please review this plan:\n\n{plan}"}
        ],
    }

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "X-Title": "Consult the Council",
        }
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"]


def check_models(models: list[str]) -> int:
    """Compare each council model ID against OpenRouter's public model list.

    Needs no API key. Returns the number of IDs that were not found.
    """
    with urllib.request.urlopen(OPENROUTER_MODELS_URL, timeout=30) as resp:
        available = {m["id"] for m in json.loads(resp.read().decode("utf-8"))["data"]}

    missing = 0
    for model_id in models:
        if model_id in available:
            print(f"OK       {model_id}")
        else:
            print(f"MISSING  {model_id}  <- not on OpenRouter; fix or remove it in council-models.md")
            missing += 1

    print(f"\n{len(models) - missing} of {len(models)} council models found on OpenRouter.")
    return missing


def query_council_member(model_id: str, plan: str, timeout: int = 120) -> tuple[str, str, str | None]:
    """Query a single council member. Returns (model_id, response, error)."""
    try:
        response = query_openrouter(model_id, plan, timeout=timeout)
        return model_id, response, None
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else str(e)
        return model_id, "", f"HTTP {e.code}: {error_body}"
    except Exception as e:
        return model_id, "", str(e)


def consult_council(
    models: list[str], plan: str, parallel: bool = True, timeout: int = 120
) -> dict[str, dict[str, str | None]]:
    """Consult all council members and return their feedback."""
    results = {}

    if parallel:
        with ThreadPoolExecutor(max_workers=len(models)) as executor:
            futures = {
                executor.submit(query_council_member, model_id, plan, timeout): model_id
                for model_id in models
            }
            for future in as_completed(futures):
                model_id, response, error = future.result()
                results[model_id] = {"response": response, "error": error}
    else:
        for model_id in models:
            model_id, response, error = query_council_member(model_id, plan, timeout)
            results[model_id] = {"response": response, "error": error}

    return results


def extract_verdict(response: str) -> str | None:
    """Extract a known verdict from a council member's response."""
    if "## Verdict" not in response:
        return None
    verdict_section = response.split("## Verdict")[-1].strip()
    verdict_line = verdict_section.split("\n")[0].upper()
    # Check longest matches first to avoid "APPROVE" matching "APPROVE WITH CHANGES"
    for verdict in KNOWN_VERDICTS:
        if verdict in verdict_line:
            return verdict
    return None


def format_council_report(plan: str, results: dict[str, dict[str, str | None]]) -> str:
    """Format council feedback into a readable report."""
    lines = [
        "# Council Feedback Report",
        "",
        "## Plan Under Review",
        "```",
        plan[:2000] + ("..." if len(plan) > 2000 else ""),
        "```",
        "",
        "---",
        ""
    ]

    verdicts = []
    for model_id, data in results.items():
        lines.append(f"## Council Member: {model_id}")
        lines.append("")

        if data["error"]:
            lines.append(f"**Error:** {data['error']}")
        else:
            lines.append(data["response"])
            verdict = extract_verdict(data["response"])
            if verdict:
                verdicts.append((model_id, verdict))

        lines.append("")
        lines.append("---")
        lines.append("")

    # Summary section
    lines.append("## Council Summary")
    lines.append("")
    if verdicts:
        lines.append("### Verdicts")
        for model_id, verdict in verdicts:
            lines.append(f"- **{model_id}**: {verdict}")

    approve_count = sum(1 for _, v in verdicts if v == "APPROVE")
    changes_count = sum(1 for _, v in verdicts if v == "APPROVE WITH CHANGES")
    revision_count = sum(1 for _, v in verdicts if v == "REQUEST REVISION")

    lines.append("")
    lines.append(f"**Consensus:** {approve_count} Approve, {changes_count} Approve with Changes, {revision_count} Request Revision")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Consult the Council of LLMs")
    parser.add_argument("--plan", type=str, help="Plan text to review")
    parser.add_argument("--plan-file", type=str, help="File containing plan to review")
    parser.add_argument("--output", type=str, help="Output file for report (default: council-feedback.md)")
    parser.add_argument("--sequential", action="store_true", help="Query models sequentially instead of in parallel")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted report")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout per model in seconds (default: 120)")
    parser.add_argument("--check-models", action="store_true",
                        help="Check council-models.md against OpenRouter's model list, then exit (no API key needed)")

    args = parser.parse_args()

    if args.check_models:
        sys.exit(1 if check_models(load_council_models()) else 0)

    # Get plan text
    if args.plan_file:
        with open(args.plan_file, "r") as f:
            plan = f.read()
    elif args.plan:
        plan = args.plan
    else:
        print("Error: Must provide --plan or --plan-file", file=sys.stderr)
        sys.exit(1)

    load_config()
    models = load_council_models()

    print(f"Consulting the council ({len(models)} members)...", file=sys.stderr)

    results = consult_council(models, plan, parallel=not args.sequential, timeout=args.timeout)

    if args.json:
        output = json.dumps(results, indent=2)
    else:
        output = format_council_report(plan, results)

    output_path = args.output or "council-feedback.md"
    with open(output_path, "w") as f:
        f.write(output)
    print(f"Report saved to {output_path}", file=sys.stderr)
    print(output)


if __name__ == "__main__":
    main()
