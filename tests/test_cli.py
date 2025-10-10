from click.testing import CliRunner
import pytest


def test_cli_list_models(monkeypatch):
    """The list-models command should run and print model names."""
    # Fake OllamaClient with list_models method
    class FakeClient:
        def __init__(self, host=None):
            pass

        async def list_models(self):
            from ollama_bench.models import Model

            return [Model(name="one"), Model(name="two")]

        async def close(self):
            return None

    # Monkeypatch the constructor used in the CLI module path
    monkeypatch.setattr("ollama_bench.cli.OllamaClient", FakeClient)

    from ollama_bench.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["list-models"])
    assert result.exit_code == 0
    # Pretty format: multi-line blocks with names present
    assert "one" in result.output
    assert "size:" in result.output


def test_cli_compact_and_no_color(monkeypatch):
    class FakeClient2:
        def __init__(self, host=None):
            pass

        async def list_models(self):
            from ollama_bench.models import Model

            return [Model(name="alpha", size="1.4 GB", parameter_size="7B", quantization_level="q4_0", family="gemma", context_length=8192)]

        async def close(self):
            return None

    monkeypatch.setattr("ollama_bench.cli.OllamaClient", FakeClient2)
    from ollama_bench.cli import cli

    runner = CliRunner()
    # compact format
    result = runner.invoke(cli, ["list-models", "--print-format", "compact"])
    assert result.exit_code == 0
    assert "alpha" in result.output
    assert "size=1.4 GB" in result.output or "1.4 GB" in result.output

    # no-color should still produce readable text
    result2 = runner.invoke(cli, ["list-models", "--print-format", "compact", "--no-color"])
    assert result2.exit_code == 0
    assert "alpha" in result2.output


def test_cli_generate(monkeypatch):
    """The generate command should run and print JSON raw response."""
    class FakeClient:
        def __init__(self, host=None):
            pass

        async def generate(self, model, prompt):
            return {"message": "ok", "model": model, "prompt": prompt}

        async def close(self):
            return None

    monkeypatch.setattr("ollama_bench.cli.OllamaClient", FakeClient)

    from ollama_bench.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["generate", "mymodel", "hello"])
    assert result.exit_code == 0
    assert '"message": "ok"' in result.output
    assert '"model": "mymodel"' in result.output
