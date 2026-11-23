# Consult the Council

A Claude Code skill that sends a plan to a panel of other AI models through [OpenRouter](https://openrouter.ai) and brings back their critiques. One OpenRouter API key covers every model: OpenAI, Google, DeepSeek, Moonshot, Qwen, xAI, Mistral and hundreds more.

## Why

Claude Code is good at making plans, but one model can miss things. This skill asks several models to review the same plan at the same time, each on its own. You get back one report with each model's analysis, concerns, recommendations and verdict (APPROVE / APPROVE WITH CHANGES / REQUEST REVISION), plus a tally of the verdicts.

Use it before a complex change, an architecture decision, or any time you want a second (and third) opinion.

## What you need

- Python 3.10 or newer (no extra packages)
- An [OpenRouter API key](https://openrouter.ai/keys) with some credit on the account

## Install

1. Clone the repo into your Claude Code skills folder:

   ```bash
   git clone https://github.com/bronsonelliott/consult-the-council.git ~/.claude/skills/consult-the-council
   ```

2. Create your private config file from the template:

   ```bash
   cd ~/.claude/skills/consult-the-council
   cp config.env.template config.env
   ```

   Nothing prints if it worked. Run `ls` and you should see `config.env` in the list. Stay in this folder for the next step.

3. Open `config.env` in a text editor. On a Mac this opens it in TextEdit:

   ```bash
   open -e config.env
   ```

   Paste your key after the `=`, then save and close the file:

   ```
   OPENROUTER_API_KEY=sk-or-v1-your-key-here
   ```

   `config.env` is in `.gitignore`, so git never commits it. You can set `OPENROUTER_API_KEY` as an environment variable instead.

4. Quit Claude Code and open it again so it loads the new skill. Type `/consult-the-council` and it should show up in the list of commands.

## Usage

### From Claude Code

Type `/consult-the-council`, or ask Claude for "council feedback" or a "multi-model review". Claude writes the plan to a file and runs the script for you.

### From the command line

Run every command in this README from the skill folder. The commands use the short path `scripts/consult_council.py`, which only works from there:

```bash
cd ~/.claude/skills/consult-the-council
```

Pass a plan inline:

```bash
python3 scripts/consult_council.py --plan "Migrate the database from Postgres to SQLite"
```

Or from a file (better for long plans):

```bash
python3 scripts/consult_council.py --plan-file plan.md
```

While it runs you'll see `Consulting the council (12 members)...`. When it finishes you'll see `Report saved to council-feedback.md`, followed by the full report. The file is saved in the folder you ran the command from. Use `--output` to save it somewhere else.

### Options

| Flag | What it does |
|------|-------------|
| `--plan TEXT` | Plan text to review |
| `--plan-file FILE` | Read the plan from a file |
| `--output FILE` | Where to save the report (default: `council-feedback.md`) |
| `--sequential` | Ask models one at a time instead of all at once |
| `--json` | Save raw JSON instead of the formatted report |
| `--timeout SECS` | Seconds to wait for each model (default: 120) |
| `--check-models` | Check every ID in `council-models.md` exists on OpenRouter, then stop. Needs no API key and costs nothing |

## Updating the models

The council is whatever is listed in **`council-models.md`**, in the skill's top folder. The script reads that file on every run, so there is nothing to restart or rebuild.

### Step by step

1. **Find the model ID.** Go to [openrouter.ai/models](https://openrouter.ai/models) and click the model you want. Copy the ID shown under its name. It always looks like `provider/model-name`, for example `openai/gpt-6.2-astra-pro`.

2. **Edit `council-models.md`.** One model ID per line.
   - To **add** a member, add a line.
   - To **remove** a member, delete its line or put `#` in front of it.
   - To **swap** a model for a newer version, replace the old ID with the new one.

   ```
   # Lines starting with # are ignored
   openai/gpt-6.2-astra-pro
   google/gemini-4-neon
   # x-ai/grok-4.7          <- commented out, so not on the council
   ```

3. **Check the list.** From the skill folder, run this. It compares every ID against OpenRouter's live model list:

   ```bash
   python3 scripts/consult_council.py --check-models
   ```

   The output looks like this:

   ```
   OK       openai/gpt-6.2-astra-pro
   MISSING  example/old-model  <- not on OpenRouter; fix or remove it in council-models.md

   11 of 12 council models found on OpenRouter.
   ```

   Fix or remove any `MISSING` line before your next review. A missing model doesn't break a review; it just shows up as an error in that model's section of the report.

### Things to know

- **The shipped list was current on 2026-11-23.** All 12 IDs passed `--check-models` that day. Run it yourself after installing, since models change often.
- **Cost scales with the list.** Each model is one paid API call per review, and the shipped list has 12 members. Prices differ a lot between models, so there's no single per-review figure. Run one review, then look at [openrouter.ai/activity](https://openrouter.ai/activity) to see what each call cost. Trim the list if you want cheaper reviews. Models ending in `:free` cost nothing but have tighter rate limits.
- **`openrouter/auto`** lets OpenRouter pick a model for each request. Remove it if you want every member to be a fixed, known model.
- **Model IDs go stale.** Providers retire and rename models. Run `--check-models` every so often, or whenever a member starts returning errors.
- **Allowed characters.** An ID must look like `provider/model-name`. Letters, numbers, `.`, `-`, `_`, `:` and `+` are allowed. Lines that don't match are skipped without a warning, so run `--check-models` after editing.
- **Fallback list.** If `council-models.md` is missing or has no valid IDs, the script falls back to three models listed as `DEFAULT_MODELS` near the top of `scripts/consult_council.py`. You normally never need to touch it.

## Output

The report has three parts:

1. **Plan Under Review**: the plan you sent (first 2,000 characters)
2. **Per-member feedback**: each model's analysis, strengths, concerns, recommendations and verdict
3. **Council Summary**: each verdict and the totals

If a model fails (API error, timeout, bad model ID), its section shows the error and the other members' feedback is still included.

## Project structure

```
consult-the-council/
  SKILL.md               # Tells Claude Code when and how to use the skill
  council-models.md      # The models on the council (edit this)
  config.env.template    # Template for your API key (copy to config.env)
  config.env             # Your API key (you create this; never committed)
  scripts/
    consult_council.py   # The script
  references/
    council-config.md    # OpenRouter API details and troubleshooting
```

## Troubleshooting

**Missing API key**: copy `config.env.template` to `config.env` and add your key. Get one at [openrouter.ai/keys](https://openrouter.ai/keys).

**Invalid model ID (HTTP 400)**: run `--check-models`, then fix the `MISSING` lines in `council-models.md`.

**Insufficient credits (HTTP 402)**: add credits at [openrouter.ai/credits](https://openrouter.ai/credits).

**Model timeout**: the default wait is 120 seconds. Use `--timeout 300` for slow reasoning models. Use `--sequential` to see which model is the slow one.

## License

MIT. See [LICENSE](LICENSE).
