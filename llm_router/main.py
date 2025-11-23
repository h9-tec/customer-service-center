import os
from typing import Any, Dict, List, Optional

import requests

from fastapi import FastAPI

from llm_router.schemas import Backend, InferenceRequest, InferenceResponse

app = FastAPI(title="LLM Router", version="0.1.0", docs_url="/docs")


def _call_ollama_chat(model: str, messages: List[Dict[str, str]], temperature: float, max_tokens: int, stream: bool) -> Optional[str]:
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    try:
        resp = requests.post(
            f"{host}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "options": {"temperature": temperature, "num_predict": max_tokens},
                "stream": stream,
            },
            timeout=60,
        )
        if not resp.ok:
            return None
        data = resp.json()
        if not data.get("message"):
            return None
        return data["message"].get("content")
    except Exception:
        return None


def _call_vllm(model: str, messages: List[Dict[str, str]], temperature: float, max_tokens: int, stream: bool) -> Optional[str]:
    vllm_url = os.environ.get("VLLM_URL")
    api_key = os.environ.get("VLLM_API_KEY", "")
    if not vllm_url:
        return None
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    try:
        resp = requests.post(
            f"{vllm_url}/v1/chat/completions",
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream,
            },
            headers=headers,
            timeout=60,
        )
        if not resp.ok:
            return None
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content")
    except Exception:
        return None


def _call_llamacpp(model: str, messages: List[Dict[str, str]], temperature: float, max_tokens: int, stream: bool) -> Optional[str]:
    llama_url = os.environ.get("LLAMACPP_URL")
    if not llama_url:
        return None
    try:
        resp = requests.post(
            f"{llama_url}/v1/chat/completions",
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream,
            },
            timeout=60,
        )
        if not resp.ok:
            return None
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content")
    except Exception:
        return None


def _select_backend(request: InferenceRequest) -> Backend:
    if request.backend:
        return request.backend
    if os.environ.get("VLLM_URL"):
        return Backend.VLLM
    if os.environ.get("LLAMACPP_URL"):
        return Backend.LLAMACPP
    return Backend.OLLAMA


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/llm/infer", response_model=InferenceResponse)
async def infer(request: InferenceRequest) -> InferenceResponse:
    """Inference endpoint with Ollama/vLLM/llama.cpp support."""
    output = None
    meta: Dict[str, Any] = {"tools_received": len(request.tools or [])}
    backend = _select_backend(request)

    stream_chunks = None
    if backend == Backend.OLLAMA:
        output = _call_ollama_chat(
            model=request.model,
            messages=[m.model_dump() for m in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=request.stream,
        )
    elif backend == Backend.VLLM:
        output = _call_vllm(
            model=request.model,
            messages=[m.model_dump() for m in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=request.stream,
        )
    elif backend == Backend.LLAMACPP:
        output = _call_llamacpp(
            model=request.model,
            messages=[m.model_dump() for m in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=request.stream,
        )

    if output is None:
        output = "LLM backend not available or returned no content."
        meta["warning"] = "backend_unavailable"

    return InferenceResponse(
        backend=backend,
        model=request.model,
        output=output,
        tool_calls=[],
        meta=meta,
        stream_chunks=stream_chunks,
    )


@app.get("/llm/ollama/models")
async def list_ollama_models() -> Dict[str, List[Dict[str, Any]]]:
    """List available Ollama models via local API."""
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    try:
        resp = requests.get(f"{ollama_host}/api/tags", timeout=5)
        if not resp.ok:
            return {"models": [], "error": resp.text, "status_code": resp.status_code}
        data = resp.json()
        return {"models": data.get("models", [])}
    except Exception as exc:  # noqa: broad-except
        return {"models": [], "error": str(exc)}


if __name__ == "__main__":
    port = int(os.environ.get("LLM_ROUTER_PORT", "8001"))
    app_env = os.environ.get("APP_ENV", "development")
    app_title = f"{app.title} ({app_env})"
    app.title = app_title
    import uvicorn

    uvicorn.run("llm_router.main:app", host="0.0.0.0", port=port, reload=True)
