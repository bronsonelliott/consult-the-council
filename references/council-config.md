# Council Configuration — OpenRouter Reference

## How It Works

All council models are queried through OpenRouter (https://openrouter.ai), a single gateway to 400+ LLMs. One API key, one request format, any model.

## API Details

| Field | Value |
|-------|-------|
| Endpoint | `https://openrouter.ai/api/v1/chat/completions` |
| Auth | `Authorization: Bearer $OPENROUTER_API_KEY` |
| Format | OpenAI-compatible (chat completions) |

### Request Format

```json
{
  "model": "openai/gpt-6.2-astra-pro",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ]
}
```

### Response Format

```json
{
  "choices": [
    {
      "message": {
        "content": "The model's response text"
      }
    }
  ]
}
```

### Headers

```
Content-Type: application/json
Authorization: Bearer sk-or-v1-your-key
X-Title: Consult the Council
```

## Choosing Models

Browse models at https://openrouter.ai/models. Each listing shows price, context length and capabilities. IDs use the format `provider/model-name`.

To change the council, follow "Updating the models" in the README: edit `council-models.md`, then run `python3 scripts/consult_council.py --check-models`.

The public model list the check uses is `GET https://openrouter.ai/api/v1/models` (no key needed).

## Troubleshooting

### Missing API Key
```
Missing OPENROUTER_API_KEY. Set it in config.env or as an environment variable.
Get a key at: https://openrouter.ai/keys
```
**Fix:** Copy `config.env.template` to `config.env` and add your key.

### Invalid Model ID
```
HTTP 400: {"error": {"message": "... is not a valid model ID"}}
```
**Fix:** Run `python3 scripts/consult_council.py --check-models`, then fix the `MISSING` lines in `council-models.md`.

### Insufficient Credits
```
HTTP 402: {"error": {"message": "Insufficient credits"}}
```
**Fix:** Add credits at https://openrouter.ai/credits.

### Model Timeout
Some models take longer to respond. The default timeout is 120 seconds per model. Use `--timeout` to override (e.g. `--timeout 300` for 5 minutes). If a model consistently times out, try a faster alternative or run with `--sequential` to debug.

### One Model Fails, Others Succeed
This is handled gracefully. The report shows the error for the failed model and includes feedback from the others. No need to re-run unless you want the missing model's input.
