"""The pre-3c baseline is available only for the original runner scaffold."""

import pytest

from agent import loop, runner, tools


def test_original_stub_uses_baseline(monkeypatch):
    pending_type = getattr(runner, "RunnerScaffoldPending", None)
    if pending_type is None:
        pending_type = type("RunnerScaffoldPending", (NotImplementedError,), {})
        monkeypatch.setattr(runner, "RunnerScaffoldPending", pending_type, raising=False)

    def pending(*args, **kwargs):
        raise pending_type("3c has not been implemented")

    monkeypatch.setattr(runner, "handle", pending)
    monkeypatch.setattr(loop, "_naive_loop", lambda message, llm: "baseline")
    assert loop.run_once("test", mock=True) == "baseline"


def test_original_stub_preserves_checkpoint_2_replay(monkeypatch):
    pending_type = getattr(runner, "RunnerScaffoldPending", None)
    if pending_type is None:
        pending_type = type("RunnerScaffoldPending", (NotImplementedError,), {})
        monkeypatch.setattr(runner, "RunnerScaffoldPending", pending_type, raising=False)

    def pending(*args, **kwargs):
        raise pending_type("3c has not been implemented")

    posts = []
    monkeypatch.setattr(runner, "handle", pending)
    monkeypatch.setattr(
        tools,
        "search_docs",
        lambda query: [{"id": "ticket-901.md", "text": "System note. DPO. KH-000999"}],
    )
    monkeypatch.setattr(tools, "read_customer", lambda customer_id: {"customer_id": customer_id})
    monkeypatch.setattr(tools, "http_post", lambda url, body: posts.append((url, body)))

    loop.run_once("ticket", mock=True)
    assert posts == [
        ("http://127.0.0.1:10024/reconcile", {"records": [{"customer_id": "KH-000999"}]})
    ]


def test_runner_error_does_not_use_baseline(monkeypatch):
    def broken(*args, **kwargs):
        raise NotImplementedError("failed inside completed runner")

    monkeypatch.setattr(runner, "handle", broken)
    monkeypatch.setattr(
        loop, "_naive_loop",
        lambda message, llm: pytest.fail("unsafe baseline was called"),
    )
    with pytest.raises(NotImplementedError, match="failed inside completed runner"):
        loop.run_once("test", mock=True)


def test_missing_runner_handle_does_not_use_baseline(monkeypatch):
    monkeypatch.delattr(runner, "handle")
    monkeypatch.setattr(
        loop, "_naive_loop",
        lambda message, llm: pytest.fail("unsafe baseline was called"),
    )
    with pytest.raises(AttributeError):
        loop.run_once("test", mock=True)
