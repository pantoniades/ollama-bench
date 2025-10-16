# ollama-bench

A CLI tool for benchmarking and testing [Ollama](https://ollama.ai/) LLM models. Compare performance metrics, list available models, and test generation across different models.

## Features

- **List Models**: View all available models on your Ollama server with detailed information
- **Generate**: Test text generation with any model
- **Benchmark**: Compare multiple models with standardized prompts and timing metrics
- **Rich Output**: Colorful, formatted terminal output using Rich library
- **Async Performance**: Built with async/await for efficient concurrent requests
- **Flexible Configuration**: Support for custom Ollama hosts via environment variables

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/ollama-bench.git
cd ollama-bench

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or install in editable mode with development dependencies
pip install -e ".[dev]"
```

### As a Package

```bash
pip install -e .
```

After installation, you can run the tool using either:
- `ollama-bench` (if installed as package)
- `python -m ollama_bench` (running as module)

## Usage

### Prerequisites

Make sure you have [Ollama](https://ollama.ai/) installed and running:

```bash
ollama serve
```

### List Available Models

View all models on your Ollama server:

```bash
ollama-bench list-models
```

Options:
- `--print-format` - Output format: `pretty` (default, multi-line) or `compact` (single-line)
- `--no-color` - Disable colored output
- `--host` - Ollama server URL (or set `OLLAMA_HOST` env var)

Examples:

```bash
# Compact format
ollama-bench list-models --print-format compact

# Plain text output
ollama-bench list-models --no-color

# Custom host
ollama-bench list-models --host http://localhost:11434
```

### Generate Text

Generate text from a specific model:

```bash
ollama-bench generate llama2 "Explain quantum computing in simple terms"
```

### Benchmark Models

Compare performance across models:

```bash
# Benchmark all models with default prompt
ollama-bench benchmark

# Benchmark specific models
ollama-bench benchmark -m llama2 -m mistral

# Use custom prompt
ollama-bench benchmark --prompt "Write a haiku about programming"

# Use prompt from file
ollama-bench benchmark --prompt-file prompts/test.txt

# Concurrent requests for faster benchmarking
ollama-bench benchmark -c 3

# Custom timeout (default 30s)
ollama-bench benchmark --timeout 60

# Show full response details
ollama-bench benchmark -r
```

The benchmark command shows:
- Model name and size
- Request status
- Elapsed time
- Prompt processing rate (tokens/s)
- Response generation rate (tokens/s)

## Configuration

### Environment Variables

- `OLLAMA_HOST` - Ollama server URL (default: system default, usually `http://localhost:11434`)
- `NO_COLOR` - Disable colored output (set to any value)

Example:

```bash
export OLLAMA_HOST=http://192.168.1.100:11434
ollama-bench list-models
```

### Global Options

- `--verbose` / `-v` - Enable debug logging for troubleshooting

```bash
ollama-bench -v benchmark -m llama2
```

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with verbose output
pytest -v
```

### Project Structure

```
ollama-bench/
├── ollama_bench/
│   ├── __init__.py       # Package version
│   ├── __main__.py       # Module entry point
│   ├── cli.py            # Click CLI commands
│   ├── client.py         # Ollama async client wrapper
│   └── models.py         # Data models
├── tests/
│   ├── test_client.py
│   ├── test_cli.py
│   └── test_smoke.py
├── pyproject.toml        # Project configuration
├── requirements.txt      # Dependencies
└── README.md            # This file
```

## Examples

### Quick Performance Comparison

```bash
# Compare two models on the same prompt
ollama-bench benchmark -m llama2:7b -m mistral:7b --prompt "What is machine learning?"
```

### Automated Testing Script

```bash
#!/bin/bash
# test_models.sh - Test all models with multiple prompts

for prompt_file in prompts/*.txt; do
    echo "Testing with $(basename $prompt_file)..."
    ollama-bench benchmark --prompt-file "$prompt_file" -c 2
done
```

### Check Model Availability

```bash
# Quickly check what models are available
ollama-bench list-models --print-format compact --no-color | grep llama
```

## Requirements

- Python 3.10+
- Ollama server (running locally or accessible via network)
- Dependencies:
  - `ollama>=0.6.0` - Official Ollama Python library
  - `click>=8.0.0` - CLI framework
  - `rich>=14.0.0` - Terminal formatting

## License

MIT

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## Troubleshooting

### "Connection refused" Error

Make sure Ollama is running:
```bash
ollama serve
```

### "Module not found" Error

Ensure you've installed dependencies:
```bash
pip install -r requirements.txt
```

### Slow Performance

Try increasing concurrency for benchmarks:
```bash
ollama-bench benchmark -c 5
```

Note: High concurrency may overload your system or Ollama server.
