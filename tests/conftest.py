"""A stub OpenAI-compatible endpoint, so no test ever reaches a live model."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from src.runners.harness import Item


def _completion_body(content: str, total_tokens: int, with_usage: bool) -> dict:
    body = {
        "id": "chatcmpl-stub",
        "object": "chat.completion",
        "created": 0,
        "model": "stub-model",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
    }
    if with_usage:
        body["usage"] = {
            "prompt_tokens": 7,
            "completion_tokens": 11,
            "total_tokens": total_tokens,
        }
    return body


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        self.server.stub.requests.append(
            {"path": self.path, "body": json.loads(raw or b"{}")}
        )

        status, body = self.server.stub._next_response()
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


class StubEndpoint:
    """Serves scripted chat-completion responses and keeps every request it got."""

    def __init__(self):
        self.requests: list[dict] = []
        self._queue: list[tuple[int, dict]] = []
        self._default: tuple[int, dict] | None = None
        self._server: ThreadingHTTPServer | None = None

    def queue_verdict(self, content, *, total_tokens=18, with_usage=True):
        """Script one successful reply, consumed by the next request."""
        self._queue.append((200, _completion_body(content, total_tokens, with_usage)))

    def queue_error(self, status=500):
        """Script one HTTP failure, consumed by the next request."""
        self._queue.append((status, {"error": {"message": "stub failure"}}))

    def always_verdict(self, content, *, total_tokens=18, with_usage=True):
        """Reply this to every request the queue does not cover."""
        self._default = (200, _completion_body(content, total_tokens, with_usage))

    def _next_response(self):
        if self._queue:
            return self._queue.pop(0)
        if self._default is not None:
            return self._default
        return 500, {"error": {"message": "stub exhausted"}}

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_address[1]}/v1"

    @property
    def bodies(self) -> list[dict]:
        return [r["body"] for r in self.requests]

    def start(self):
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self._server.stub = self
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def stop(self):
        self._server.shutdown()
        self._server.server_close()


@pytest.fixture
def stub(monkeypatch):
    endpoint = StubEndpoint()
    endpoint.start()
    monkeypatch.setenv("OPENAI_BASE_URL", endpoint.base_url)
    monkeypatch.setenv("OPENAI_API_KEY", "stub-key")
    yield endpoint
    endpoint.stop()


@pytest.fixture
def recorded_sleeps() -> list[float]:
    """Collects what the harness asked to sleep for, in place of wall-clock."""
    return []


@pytest.fixture
def item() -> Item:
    return Item(
        id="q001",
        question="Why is the sky blue?",
        response_a="Rayleigh scattering favours short wavelengths.",
        response_b="Because blue is the ocean's reflection.",
    )
