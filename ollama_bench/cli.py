"""Simple Click CLI to call the Ollama client and print raw results.

Provides a global --verbose / -v flag to enable DEBUG logging.
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Optional, Sequence, List

from .models import Model

import click

from .client import OllamaClient
from rich.console import Console
from asyncio import TimeoutError

logger = logging.getLogger("ollama_bench")

_CONSOLE = Console()


# Default prompt used by the benchmark command when none supplied
DEFAULT_PROMPT = (
    "Briefly explain plate tectonics in one paragraph suitable for a general audience, "
    "highlighting causes and why it matters for Earth's geography."
)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def cli(verbose: bool) -> None:
    """ollama-bench CLI"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logger.info(f"Starting ollama-bench CLI at {now}, verbose={verbose}")

def _print_models(models: Sequence[Model], fmt: str = "pretty", color: bool = True) -> None:
    """Print models in either 'pretty' (multi-line) or 'compact' (single-line) format.

    color: whether to use color/ANSI Rich formatting (respects NO_COLOR env var).
    """
    console = Console(no_color=not color, force_terminal=color)

    if fmt == "pretty":
        for m in models:
            console.print(f"[bold green]{m.name}[/bold green]")
            console.print(f"  [magenta]size:[/magenta] {m.size or '-'}")
            console.print(f"  [yellow]params:[/yellow] {m.parameter_size or '-'}  [blue]quant:[/blue] {m.quantization_level or '-'}")
            console.print(f"  [white]family:[/white] {m.family or '-'}  [cyan]ctx:[/cyan] {m.context_length or '-'}")
            console.print("")

    else:  # compact
        for i, m in enumerate(models, start=1):
            console.print(f"[cyan]{i}[/cyan] [green]{m.name}[/green]  [magenta]{m.size or '-'}[/magenta]  [yellow]{m.parameter_size or '-'}[/yellow]  [blue]{m.quantization_level or '-'}[/blue]  [white]{m.family or '-'}[/white] [cyan]{m.context_length or '-'}[/cyan]")


@cli.command("list-models")
@click.option("--host", envvar="OLLAMA_HOST", help="Ollama host URL", default=None)
@click.option("--print-format", type=click.Choice(["pretty", "compact"]), default="pretty", help="Output format")
@click.option("--no-color", is_flag=True, help="Disable colored output")
def list_models(host: Optional[str], print_format: str, no_color: bool) -> None:
    """List models from the ollama server."""

    async def _main():
        client = OllamaClient(host=host)
        try:
            models = await client.list_models()
            # Determine color availability: user flag overrides Rich
            color_enabled = (not no_color) and ("NO_COLOR" not in __import__("os").environ)
            _print_models(models, fmt=print_format, color=color_enabled)
        except Exception as exc:  # noqa: BLE001 - surface to user and log
            logger.exception("list-models failed")
            click.echo(f"Error: {exc}", err=True)
            sys.exit(1)
        finally:
            try:
                await client.close()
            except Exception:
                logger.debug("Error closing client", exc_info=True)

    asyncio.run(_main())


@cli.command("generate")
@click.argument("model")
@click.argument("prompt")
@click.option("--host", envvar="OLLAMA_HOST", help="Ollama host URL", default=None)
def generate(model: str, prompt: str, host: Optional[str]) -> None:
    """Generate from MODEL using PROMPT and print raw response."""

    async def _main():
        client = OllamaClient(host=host)
        try:
            resp = await client.generate(model, prompt)
            click.echo(json.dumps({"raw": resp}, default=str, indent=2))
        except Exception as exc:
            logger.exception("generate failed")
            click.echo(f"Error: {exc}", err=True)
            sys.exit(1)
        finally:
            try:
                await client.close()
            except Exception:
                logger.debug("Error closing client", exc_info=True)

    asyncio.run(_main())


@cli.command("benchmark")
@click.option("--prompt", "prompt_text", help="Prompt text to send to each model")
@click.option("--prompt-file", "prompt_file", type=click.Path(exists=True), help="File containing prompt to send")
@click.option("-c", "--concurrent", "concurrency", type=int, default=1, help="Number of concurrent requests")
@click.option("--timeout", "timeout", type=float, default=30.0, help="Per-request timeout in seconds")
@click.option('-m', '--model', multiple=True, help='Model(s) to benchmark')
@click.option("--host", envvar="OLLAMA_HOST", help="Ollama host URL", default=None)
@click.option("-r", "--response", "response", help="Whether to print full response", default=False, is_flag=True)
def benchmark(prompt_text: Optional[str], prompt_file: Optional[str], concurrency: int, timeout: float, model: List[str], host: Optional[str], response: bool ) -> None:
    """Send a prompt to every model and report API stats plus timing.

    This is a minimal implementation: sequential by default and limited
    concurrency when --concurrent > 1. It prints the raw returned stats
    from the API along with elapsed time per model.
    """

    # If no prompt supplied, use default prompt
    if not prompt_text and not prompt_file:
        prompt_text = DEFAULT_PROMPT

    if prompt_file:
        with open(prompt_file, "r", encoding="utf-8") as fh:
            prompt_text = fh.read()

    async def _main():
        client = OllamaClient(host=host)
        try:
            all_models = await client.list_models()
            model_names = [m.name for m in all_models]
            if model:
                selected_models = [m for m in all_models if m.name in model]
                if not selected_models:
                    raise ValueError(f"No matching models found for names: {model}. Available models: {model_names}")
                unknown = [item for item in model if item not in model_names]
                if unknown:
                    logger.warning(f"Warning: Unknown model names specified: {unknown}. \nAvailable models: {model_names}")
            else:
                selected_models = all_models
            # Simple worker that calls generate and times it
            async def run_for_model(m: Model) -> dict:
                start = asyncio.get_event_loop().time()
                try:
                    # Respect timeout per request
                    coro = client.generate(m.name, prompt_text)
                    resp = await asyncio.wait_for(coro, timeout=timeout)
                    status = "ok"
                except TimeoutError as te:
                    resp = {"error": "Generate timed out"}
                    status = "timeout"
                    logger.error(f"Timeout generating for model {m.name} after {timeout}s")
                except Exception as exc:
                    resp = {"error": str(exc)}
                    status = "error"
                    logger.error(f"Error generating for model {m.name}: {type(exc)}")
                elapsed = asyncio.get_event_loop().time() - start
                return {"model": m, "status": status, "elapsed": elapsed, "response": resp}

            results = []
            if concurrency <= 1:
                for m in selected_models:
                    r = await run_for_model(m)
                    results.append(r)
            else:
                # Limited concurrency
                sem = asyncio.Semaphore(concurrency)

                async def sem_task(m: Model):
                    async with sem:
                        return await run_for_model(m)

                tasks = [asyncio.create_task(sem_task(m)) for m in selected_models]
                for t in asyncio.as_completed(tasks):
                    results.append(await t)

            # Print results
            for r in results:
                current_model = r["model"]
                if r["status"] != "ok":
                    click.echo(f"Model {current_model.name} {r['status']} after {r['elapsed']:.3f}s: {r['response']['error']}\n'") 
                    continue
                click.echo( current_model.name)
                click.echo(f"  status: {r['status']}")
                click.echo(f"  size: {( current_model.size / 1024**3):.2f} GB")
                click.echo(f"  elapsed: {r['elapsed']:.3f}s")
                click.echo(f"  prompt_eval_count: {r['response'].get('prompt_eval_count', '-')}")
                click.echo(f"  prompt rate: {(r['response']['prompt_eval_count']/ r['response']['prompt_eval_duration']*(10**9)):.2f} tokens/s")
                click.echo(f"  response rate: {(r['response']['eval_count']/ r['response']['eval_duration']*(10**9)):.3f} tokens/s")
                response and click.echo(f"  response: {json.dumps(r['response'], default=str, indent=2)}")
                click.echo("")

        except Exception as exc:
            logger.exception("benchmark failed")
            click.echo(f"Error: {exc}", err=True)
            sys.exit(1)
        finally:
            try:
                await client.close()
            except Exception:
                logger.debug("Error closing client", exc_info=True)

    asyncio.run(_main())


if __name__ == "__main__":
    cli()

