from __future__ import annotations

import json
import uuid

import httpx
import typer

app = typer.Typer(help="Deep Agents CLI: frontend can call this CLI, CLI then streams from server via SSE.")


@app.command()
def chat(
    message: str = typer.Argument(..., help="User message"),
    server_url: str = typer.Option("http://127.0.0.1:8000", help="Server base URL"),
    session_id: str = typer.Option("", help="Optional session id"),
) -> None:
    sid = session_id or str(uuid.uuid4())
    payload = {"session_id": sid, "user_input": message}

    with httpx.Client(timeout=None) as client:
        with client.stream("POST", f"{server_url}/v1/chat/stream", json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                if line.startswith("event:"):
                    event = line.removeprefix("event:").strip()
                    if event == "start":
                        typer.echo(f"\n[session] {sid}")
                    continue
                if line.startswith("data:"):
                    data = line.removeprefix("data:").strip()
                    if data == "[DONE]":
                        typer.echo("\n")
                        break
                    typer.echo(data, nl=False)


@app.command()
def request_json(
    request_json: str = typer.Argument(..., help='Raw JSON string, e.g. "{\"message\":\"hello\"}"'),
    server_url: str = typer.Option("http://127.0.0.1:8000", help="Server base URL"),
) -> None:
    """Convenience entrypoint for web frontend wrappers that call CLI with raw JSON."""
    obj = json.loads(request_json)
    message = obj.get("message", "")
    session_id = obj.get("session_id", "")
    chat(message=message, server_url=server_url, session_id=session_id)


if __name__ == "__main__":
    app()
