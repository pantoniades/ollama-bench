# ollama-bench

Benchmark and evaluate [Ollama](https://ollama.ai/) LLM models. Compare performance, test multiple prompts, export results for quality evaluation.

## Features

- **JSON output** (default) - pipe results to (e.g.) Claude/GPT/Gemini for quality evaluation
- **Multiple prompts** - test models across diverse inputs
- **Performance metrics** - tokens/sec, latency, response time
- **Concurrent requests** - async execution for volume benchmarking
- **List models** - view available models with details

## Installation

```bash
git clone https://github.com/pantoniades/ollama-bench.git
cd ollama-bench
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Verify venv is activated (should see (.venv) in prompt)
pip install --upgrade pip
pip install -e .

# Verify installation
python verify_install.py
```

**Note:**
- Requires pip 21.3+ for pyproject.toml support
- **IMPORTANT:** Always activate the venv before running commands
- If you get "module not found" errors, your venv is not activated
- Run `python verify_install.py` anytime to check your setup

**If `ollama-bench` command not found after install:**
```bash
# Option 1: Use python -m instead
python -m ollama_bench benchmark

# Option 2: Check if venv is activated (should see (.venv) in prompt)
source .venv/bin/activate  # or deactivate and reactivate

# Option 3: Use full path
.venv/bin/ollama-bench benchmark
```

## Prerequisites

Ensure [Ollama](https://ollama.ai/) is running:

```bash
ollama serve
```

## Quick Start

```bash
# Benchmark all models (outputs JSON)
ollama-bench benchmark
# Or if command not found: python -m ollama_bench benchmark

# Benchmark specific models with multiple prompts
ollama-bench benchmark -P prompts.txt -m llama2 -m mistral -r -o results.json

# Then evaluate with Claude
claude "Rate these LLM responses: $(cat results.json)"
```

## Commands

### benchmark

```bash
# Basic usage
ollama-bench benchmark                    # All models, default prompt, JSON output
ollama-bench benchmark -m llama2          # Specific model
ollama-bench benchmark --prompt "..."     # Custom prompt
ollama-bench benchmark -P prompts.txt     # Multiple prompts (one per line)

# Output control
ollama-bench benchmark -o results.json    # Save to file
ollama-bench benchmark -f text            # Text format instead of JSON
ollama-bench benchmark -r                 # Include full response text (defualts to results only)

# Performance
ollama-bench benchmark -c 3               # Run 3 requests concurrently
ollama-bench benchmark -t 60              # 60 second timeout

# Combined example
ollama-bench benchmark -P prompts.txt -m llama2 -m mistral -r -o results.json -c 2
```

**Options:**
- `--prompt TEXT` - Single prompt text
- `-P, --prompts-file PATH` - File with prompts (one per line)
- `-m, --model TEXT` - Specific model(s) to test (repeatable)
- `-c, --concurrent INT` - Concurrent requests (default: 1)
- `--concurrency-mode [global|per-model]` - How concurrency works (default: per-model)
  - `per-model`: Run N prompts concurrently for each model (tests model's concurrent handling)
  - `global`: Run N total tasks concurrently across all models
- `-t, --timeout FLOAT` - Timeout in seconds (default: 30)
- `-f, --format [json|text]` - Output format (default: json)
- `-o, --output PATH` - Write to file instead of stdout
- `-r, --response` - Include full response text
- `--exclude-errors` - Don't write failed results to output
- `--errors-only` - Only write failed results (useful for debugging)
- `-H, --host TEXT` - Ollama server URL (or set `OLLAMA_HOST`)

### list-models (more info & formatting than `ollama list`)

```bash
ollama-bench list-models              # Pretty format
ollama-bench list-models -f compact   # One line per model
ollama-bench list-models -n           # No color
```

**Options:**
- `-f, --print-format [pretty|compact]` - Output format (default: pretty)
- `-n, --no-color` - Disable colored output
- `-H, --host TEXT` - Ollama server URL

### generate

```bash
ollama-bench generate llama2 "Explain quantum computing"
```

## JSON Output Format

**Success:**
```json
{
  "config": {
    "prompts": ["What is 2+2?"],
    "models": ["llama2"],
    "concurrency": 1,
    "concurrency_mode": "per-model",
    "timeout": 30.0
  },
  "results": [
    {
      "model": "llama2",
      "prompt": "What is 2+2?",
      "status": "ok",
      "elapsed": 1.234,
      "metrics": {
        "prompt_eval_count": 10,
        "eval_count": 25,
        "prompt_tokens_per_sec": 123.45,
        "response_tokens_per_sec": 67.89
      },
      "response": "The answer is 4."
    }
  ]
}
```

**Error:**
```json
{
  "model": "broken-model",
  "prompt": "What is 2+2?",
  "status": "error",
  "elapsed": 0.123,
  "error": {
    "type": "ConnectionError",
    "message": "Connection refused",
    "model": "broken-model",
    "prompt": "What is 2+2?"
  }
}
```

## Configuration

### Environment Variables

- `OLLAMA_HOST` - Server URL (default: http://localhost:11434)
- `NO_COLOR` - Disable colored output

### Global Options

- `-v, --verbose` - Enable debug logging (must come before subcommand)

```bash
ollama-bench -v benchmark -m llama2  # ✅ Correct
ollama-bench benchmark -v -m llama2  # ❌ Wrong
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v
```

## Example Workflow

```bash
# Create prompts file
cat > prompts.txt << EOF
What is 2+2?
Explain quantum computing in one sentence.
Write a haiku about programming.
What is the capital of France?
EOF

# Benchmark models with full responses (per-model concurrency)
ollama-bench benchmark -P prompts.txt -m llama2 -m mistral -r -c 3 -o results.json

# Test concurrent load handling: run 3 prompts at once per model
ollama-bench benchmark -P prompts.txt -c 3 --concurrency-mode per-model

# Only save successful results
ollama-bench benchmark -P prompts.txt --exclude-errors -o results.json

# Debug: only show errors
ollama-bench benchmark -P prompts.txt --errors-only -f text

# Evaluate quality with Claude
claude "Review these LLM benchmark results and rate each response for accuracy and quality: $(cat results.json)"
```

## Requirements

- Python 3.10+
- Ollama server
- Dependencies: `ollama`, `click`, `rich` (auto-installed)

## Troubleshooting

**"click not found" or "module not found":**
```bash
# Your venv is not activated. Activate it:
source .venv/bin/activate  # You should see (.venv) in prompt

# Verify it worked:
python -c "import click; print('Dependencies loaded')"
```

**Command not found:** Use `python -m ollama_bench` instead of `ollama-bench`, or ensure venv is activated

**Connection refused:** Ensure Ollama is running (`ollama serve`)

## License

MIT
