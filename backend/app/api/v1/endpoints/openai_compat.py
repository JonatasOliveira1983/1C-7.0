"""
BASE Tecnologica — OpenAI Compatible API (OpenBot & External Integrations)
===================================================================
Fornece endpoints no padrão oficial OpenAI (/v1/chat/completions e /v1/models)
para que o OpenBot e outros clientes se conectem diretamente à nossa IA Local Dedicada
(Qwen3 1.7B CPU, no-think) sem necessitar do 9Router nem de chaves da nuvem.
O nome de modelo pedido e' ecoado (servidor de modelo unico, modo conversa).
"""
import time
import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.services.local_llm_service import local_llm_service

router = APIRouter()


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = "qwen3-1.7b-instruct"
    messages: List[Dict[str, Any]]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 600
    stream: Optional[bool] = False

    class Config:
        extra = "ignore"


@router.get("/models", summary="Lista os modelos de IA disponíveis (OpenAI Standard)")
def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "qwen3-1.7b-instruct",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "local",
                "permission": [],
                "root": "qwen3-1.7b-instruct",
                "parent": None
            },
            {
                "id": "qwen2.5-1.5b-instruct",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "local",
                "permission": [],
                "root": "qwen3-1.7b-instruct",
                "parent": None
            }
        ]
    }


@router.post("/chat/completions", summary="Endpoint de Chat Completions padrão OpenAI")
async def chat_completions(req: ChatCompletionRequest):
    if not local_llm_service.is_available():
        raise HTTPException(status_code=503, detail="Modelo local ainda não baixado ou indisponível.")

    # Normalizar mensagens
    formatted_messages = []
    for m in req.messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        # Se vier array de blocos de conteúdo (estilo multimodal), achatar para texto
        if isinstance(content, list):
            text_parts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"]
            content = " ".join(text_parts)
        formatted_messages.append({"role": role, "content": str(content)})

    if req.stream:
        def sse_generator():
            try:
                gen = local_llm_service.create_chat_completion(
                    messages=formatted_messages,
                    temperature=req.temperature or 0.7,
                    max_tokens=req.max_tokens or 600,
                    stream=True,
                    model=req.model or "qwen3-1.7b-instruct"
                )
                for chunk in gen:
                    yield f"data: {json.dumps(chunk)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                err = {"error": {"message": str(e), "type": "server_error"}}
                yield f"data: {json.dumps(err)}\n\n"

        return StreamingResponse(sse_generator(), media_type="text/event-stream")

    try:
        import asyncio
        completion = await asyncio.to_thread(
            local_llm_service.create_chat_completion,
            messages=formatted_messages,
            temperature=req.temperature or 0.7,
            max_tokens=req.max_tokens or 600,
            stream=False,
            model=req.model or "qwen3-1.7b-instruct"
        )
        return JSONResponse(content=completion)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na inferência da IA local: {e}")
