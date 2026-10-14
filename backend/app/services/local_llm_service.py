"""
BASE Tecnologica — Local LLM Service (Embutido no Python com Llama-CPP)
==================================================================
Execucao local nativa em CPU (sem GPU, sem Ollama, sem APIs externas).
Modelo quantizado Qwen3 1.7B Instruct GGUF (Q4_K_M ~1.1GB).
Qwen3 tem thinking-mode por padrao: aqui ele e desligado via prefill
de bloco think vazio (equivale a enable_thinking=false), senao o modelo
gasta todos os tokens pensando em ingles antes de responder.
"""
import os
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import threading

MODELS_DIR = Path(__file__).resolve().parent.parent / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_REPO_ID = "unsloth/Qwen3-1.7B-GGUF"
MODEL_FILENAME = "Qwen3-1.7B-Q4_K_M.gguf"
LOCAL_MODEL_PATH = MODELS_DIR / MODEL_FILENAME
# ID anunciado na API OpenAI-compat (/v1/models). O anterior e' mantido como alias.
QWEN3_MODEL_ID = "qwen3-1.7b-instruct"
LEGACY_MODEL_ID = "qwen2.5-1.5b-instruct"

_model_instance = None
_model_lock = threading.Lock()
# llama-cpp nao aceita inferencia concorrente no mesmo modelo
_infer_lock = threading.Lock()
_load_status = {"status": "NOT_LOADED", "error": None, "last_latency_ms": None}

_LT = chr(60)
_GT = chr(62)
_IM_START = _LT + "|im_start|>"
_IM_END = _LT + "|im_end|>"
_THINK_OPEN = _LT + "think" + _GT
_THINK_CLOSE = _LT + "/think" + _GT
# Prefill que desliga o thinking do Qwen3 (igual ao template com enable_thinking=false)
_NOTHINK_PREFILL = _THINK_OPEN + "\n\n" + _THINK_CLOSE + "\n\n"

_THINK_RE = re.compile(re.escape(_THINK_OPEN) + r".*?" + re.escape(_THINK_CLOSE), re.DOTALL)


def download_model_if_needed() -> Path:
    """Garante que o arquivo GGUF do modelo existe localmente."""
    if LOCAL_MODEL_PATH.exists() and LOCAL_MODEL_PATH.stat().st_size > 500_000_000:
        return LOCAL_MODEL_PATH

    print(f"[*] Baixando modelo local {MODEL_FILENAME} (~1.1 GB) de {MODEL_REPO_ID}...")
    try:
        from huggingface_hub import hf_hub_download
        downloaded_path = hf_hub_download(
            repo_id=MODEL_REPO_ID,
            filename=MODEL_FILENAME,
            local_dir=str(MODELS_DIR),
        )
        print(f"[OK] Download concluido: {downloaded_path}")
        return Path(downloaded_path)
    except Exception as e:
        print(f"[!] Erro ao baixar modelo via huggingface_hub: {e}")
        import urllib.request
        url = f"https://huggingface.co/{MODEL_REPO_ID}/resolve/main/{MODEL_FILENAME}"
        print(f"[*] Tentando download direto de {url}...")
        urllib.request.urlretrieve(url, str(LOCAL_MODEL_PATH))
        return LOCAL_MODEL_PATH


def build_qwen3_prompt(messages: List[Dict[str, str]]) -> str:
    """Monta o prompt ChatML manualmente com prefill no-think no turno assistant."""
    parts = []
    for m in messages or []:
        role = m.get("role", "user") if isinstance(m, dict) else "user"
        content = m.get("content", "") if isinstance(m, dict) else str(m)
        if role not in ("system", "user", "assistant"):
            role = "user"
        parts.append(f"{_IM_START}{role}\n{content}\n{_IM_END}\n")
    parts.append(f"{_IM_START}assistant\n{_NOTHINK_PREFILL}")
    return "".join(parts)


def strip_think(text: str) -> str:
    """Remove qualquer bloco think residual (caso o modelo abra um novo)."""
    if not text:
        return text
    text = _THINK_RE.sub("", text)
    # Se sobrou abertura sem fechamento, corta tudo a partir dela
    idx = text.find(_THINK_OPEN)
    if idx >= 0:
        text = text[:idx]
    return text.strip()


class LocalLLMService:
    """Gerenciador Singleton da LLM local rodando em CPU."""

    def __init__(self):
        self.model_path = LOCAL_MODEL_PATH

    def is_available(self) -> bool:
        """Verifica se o arquivo do modelo esta baixado e pronto."""
        return self.model_path.exists() and self.model_path.stat().st_size > 500_000_000

    def get_model(self):
        """Inicializa e retorna o modelo em memoria (Singleton lazy load)."""
        global _model_instance, _load_status
        if _model_instance is not None:
            return _model_instance

        with _model_lock:
            if _model_instance is not None:
                return _model_instance

            if not self.is_available():
                download_model_if_needed()

            print("[*] Carregando modelo Qwen3 1.7B GGUF na CPU (4 threads, no-think)...")
            _load_status["status"] = "LOADING"
            t0 = time.time()
            try:
                from llama_cpp import Llama
                _model_instance = Llama(
                    model_path=str(self.model_path),
                    n_ctx=4096,
                    n_threads=4,
                    n_batch=512,
                    verbose=False
                )
                load_time = round(time.time() - t0, 2)
                _load_status["status"] = "READY"
                _load_status["load_time_s"] = load_time
                print(f"[OK] Modelo Qwen3 carregado na CPU em {load_time}s!")
                return _model_instance
            except Exception as e:
                _load_status["status"] = "ERROR"
                _load_status["error"] = str(e)
                print(f"[!] Falha ao carregar LlamaCpp: {e}")
                return None

    def generate(self, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 1000) -> Optional[str]:
        """Executa a inferencia local (prompt ChatML com think vazio pre-preenchido)."""
        model = self.get_model()
        if not model:
            return None

        prompt = build_qwen3_prompt(messages)
        t0 = time.time()
        try:
            with _infer_lock:
                response = model.create_completion(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stop=[_IM_END],
                    stream=False
                )
            elapsed_ms = round((time.time() - t0) * 1000, 1)
            _load_status["last_latency_ms"] = elapsed_ms
            content = response["choices"][0]["text"]
            if content:
                content = strip_think(content).replace("\ufffd", "").strip()
            return content
        except Exception as e:
            print(f"[LocalLLMService] Erro na geracao local: {e}")
            return None

    def create_chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 600, stream: bool = False, model: Optional[str] = None):
        """Compat OpenAI (dict chat.completion ou gerador de chunks SSE) sobre o prompt no-think.

        O nome de modelo pedido e' apenas ecoado na resposta (o servidor local
        tem um unico modelo); parametros extras do protocolo (tools, tool_choice,
        response_format) sao ignorados — o Qwen local opera em modo conversa.
        """
        if stream:
            return self._stream_chat_completion(messages, temperature, max_tokens, model)
        llm = self.get_model()
        if not llm:
            raise RuntimeError("Modelo local nao pode ser carregado.")
        model_id = model or QWEN3_MODEL_ID
        prompt = build_qwen3_prompt(messages)
        base = {
            "id": f"chatcmpl-local-{int(time.time() * 1000)}",
            "created": int(time.time()),
            "model": model_id,
        }
        with _infer_lock:
            resp = llm.create_completion(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=[_IM_END],
                stream=False
            )
        choice = (resp.get("choices") or [{}])[0]
        content = strip_think(choice.get("text", "") or "").replace("\ufffd", "").strip()
        usage = resp.get("usage") or {}
        return {
            **base,
            "object": "chat.completion",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": choice.get("finish_reason") or "stop",
            }],
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        }

    def _stream_chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 600, model: Optional[str] = None):
        """Gerador de chunks chat.completion.chunk (formato SSE do AI SDK)."""
        llm = self.get_model()
        if not llm:
            raise RuntimeError("Modelo local nao pode ser carregado.")
        base = {
            "id": f"chatcmpl-local-{int(time.time() * 1000)}",
            "created": int(time.time()),
            "model": model or QWEN3_MODEL_ID,
            "object": "chat.completion.chunk",
        }
        prompt = build_qwen3_prompt(messages)
        with _infer_lock:
            gen = llm.create_completion(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=[_IM_END],
                stream=True
            )
            first = True
            for chunk in gen:
                try:
                    piece = chunk["choices"][0].get("text", "")
                    finish = chunk["choices"][0].get("finish_reason")
                except Exception:
                    piece, finish = "", None
                piece = (piece or "").replace("\ufffd", "")
                delta = {"content": piece} if piece else {}
                if first:
                    delta = {"role": "assistant", **delta}
                    first = False
                yield {
                    **base,
                    "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
                }
                if finish:
                    break
            else:
                yield {
                    **base,
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                }

    def get_status(self) -> Dict[str, Any]:
        """Retorna o status operacional da IA local."""
        return {
            "engine": "llama-cpp-python (Embutido, no-think)",
            "model_name": MODEL_FILENAME,
            "status": _load_status.get("status", "NOT_LOADED"),
            "model_downloaded": self.is_available(),
            "model_size_mb": round(self.model_path.stat().st_size / (1024*1024), 1) if self.model_path.exists() else 0,
            "last_latency_ms": _load_status.get("last_latency_ms"),
            "hardware": "CPU (4 threads AVX2)",
            "ram_consumption_estimated": "1.4 GB"
        }


local_llm_service = LocalLLMService()
