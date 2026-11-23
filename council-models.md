# Council Models: the models that review your plans.
#
# How to update:
#   1. Find model IDs at https://openrouter.ai/models (click a model, copy the ID
#      shown under its name, e.g. openai/gpt-6.2-astra-pro).
#   2. Put one ID per line below. Add a line to add a member; delete or
#      comment out (#) a line to remove one.
#   3. Check your list:  python3 scripts/consult_council.py --check-models
#
# Every line is one paid API call per review, so more members cost more.
# Lines starting with # are ignored.

openrouter/auto
openai/gpt-6.2-astra-pro
google/gemini-4-neon
deepseek/deepseek-v4.1-flash-1017
moonshotai/kimi-k3.1-pro
minimax/minimax-m3
qwen/qwen4-max
z-ai/glm-5.3
x-ai/grok-4.7
nvidia/nemotron-3-ultra-550b-a55b:free
meta/muse-wonder
mistralai/mistral-large-4-0
