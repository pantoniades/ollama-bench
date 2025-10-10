"""Async wrapper around the `ollama` library.

This module requires the `ollama` package and its `AsyncClient` API.
It validates the client surface at startup and logs useful debug
information when requested.
"""
from __future__ import annotations

import inspect
import logging
from typing import Any, Dict, List, Optional

import ollama
from .models import Model

logger = logging.getLogger(__name__)


class OllamaClient:
    """Simple Async wrapper around the documented `ollama.AsyncClient` API.

    This simplified client assumes the `ollama` library exposes the
    documented `AsyncClient` methods (for example `list`, `generate`,
    `chat`). It no longer performs runtime discovery of method names.
    """

    def __init__(self, host: Optional[str] = None):
        self.host = host
        self._client = ollama.AsyncClient(host=self.host) 

    async def close(self) -> None:
        if self._client is None:
            return
        # Some implementations provide an async aclose(), others a sync close().
        if hasattr(self._client, "aclose"):
            await self._client.aclose()  # type: ignore[arg-type]
        elif hasattr(self._client, "close"):
            # close() may be sync or async; call and await only if awaitable.
            res = self._client.close()
            if inspect.isawaitable(res):
                await res

    async def list_models(self) -> List[Model]:
        """Return a list of `Model` objects available on the server.

        The ollama client may return several shapes:
        - a list of dicts
        - an async generator yielding parts (dict/list)
        - an object with a `models` attribute (pydantic-like)
        - an object with .dict() that returns one of the above
        """
        logger.debug("Fetching models from ollama server")
        raw = await self._client.list()
        logger.debug("Raw models data: %s", raw)

        items: List[Any] = []

        def extend_from(obj: Any) -> None:
            if obj is None:
                return
            # If obj is a mapping with 'models'
            if isinstance(obj, dict) and "models" in obj:
                models_part = obj.get("models") or []
                if isinstance(models_part, list):
                    items.extend(models_part)
                else:
                    items.append(models_part)
                return
            # If obj itself is a list, extend
            if isinstance(obj, list):
                items.extend(obj)
                return
            # If obj exposes a .models attribute (pydantic-like), try to use it
            if hasattr(obj, "models"):
                try:
                    m = getattr(obj, "models")
                    if m is None:
                        return
                    if isinstance(m, list):
                        items.extend(m)
                    else:
                        items.append(m)
                    return
                except Exception:
                    pass
            # Fallback: append the object as-is
            items.append(obj)

        # If streaming async iterator
        if inspect.isasyncgen(raw) or inspect.isgenerator(raw):
            async for part in raw:  # type: ignore
                # If part is a typed object with dict(), prefer its dict
                if hasattr(part, "dict") and callable(getattr(part, "dict")):
                    try:
                        part = part.dict()
                    except Exception:
                        pass
                extend_from(part)
        else:
            # If the raw object has a .dict() method, try that first
            if hasattr(raw, "dict") and callable(getattr(raw, "dict")):
                try:
                    raw_dict = raw.dict()
                    extend_from(raw_dict)
                except Exception:
                    extend_from(raw)
            else:
                extend_from(raw)

        # Normalize each item into a Model
        models: List[Model] = [Model.from_dict(it) for it in items]
        return models

    async def generate(self, model: str, prompt: str, **kwargs) -> Any:
        """Generate text from `model` using `prompt` and return raw response."""
        logger.debug("Generating (model=%s) prompt_len=%d kwargs=%s", model, len(prompt), kwargs)
        # Call the documented AsyncClient.generate() API. When stream=True the
        # call may return an async iterable; in that case return the iterable
        # so callers can iterate over streamed chunks.
        resp = await self._client.generate(model=model, prompt=prompt, **kwargs)
        logger.debug("Received generate response: %s", resp)
        # If streaming, return the async generator as-is so caller can consume it.
        if inspect.isasyncgen(resp) or inspect.isgenerator(resp):
            return resp  # type: ignore[return-value]
        return resp
