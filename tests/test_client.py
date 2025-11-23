import asyncio

import asyncio


def test_list_models_returns_names(monkeypatch):
    """Ensure OllamaClient.list_models extracts names from list response."""
    # Create a fake AsyncClient with an async list() method that returns a list
    class FakeAsyncClient:
        def __init__(self, host=None):
            self.host = host

        async def list(self):
            return [{"name": "gemma3"}, {"name": "gemma2"}]

        async def aclose(self):
            return None

    monkeypatch.setattr("ollama.AsyncClient", FakeAsyncClient)

    from unladen_swallm.client import OllamaClient
    from unladen_swallm.models import Model

    client = OllamaClient(host=None)
    models = asyncio.run(client.list_models())
    assert [m.name for m in models] == ["gemma3", "gemma2"]
    assert all(isinstance(m, Model) for m in models)
    asyncio.run(client.close())


def test_list_models_handles_streaming(monkeypatch):
    """If the underlying API streams results (async generator), client should consume it."""
    class FakeAsyncClient:
        def __init__(self, host=None):
            self.host = host

        async def list(self):
            async def gen():
                yield {"name": "stream1"}
                yield {"name": "stream2"}

            return gen()

        async def aclose(self):
            return None

    monkeypatch.setattr("ollama.AsyncClient", FakeAsyncClient)

    from unladen_swallm.client import OllamaClient

    from unladen_swallm.client import OllamaClient
    from unladen_swallm.models import Model

    client = OllamaClient(host=None)
    models = asyncio.run(client.list_models())
    assert [m.name for m in models] == ["stream1", "stream2"]
    assert all(isinstance(m, Model) for m in models)
    asyncio.run(client.close())
