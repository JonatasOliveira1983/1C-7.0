"""
Base Tecnológica — DeepSeek LLM Service.
Motor de inteligência de alta velocidade e profundidade analítica.
Compatível com a especificação OpenAI (/chat/completions) e com fallback offline resiliente para Qwen3 local.
"""
import os
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")
DEFAULT_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")


class DeepSeekService:
    def __init__(self, api_key: str = DEEPSEEK_API_KEY):
        self.api_key = api_key
        self.model = DEFAULT_MODEL
        self.timeout = 15

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 800,
        model: Optional[str] = None
    ) -> Optional[str]:
        """Envia requisição para a API DeepSeek e retorna o conteúdo gerado."""
        if not self.api_key:
            return None

        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            DEEPSEEK_API_URL,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "Base-Tecnologica-Agent/2.0"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status == 200:
                    resp_body = response.read().decode("utf-8")
                    result = json.loads(resp_body)
                    choices = result.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "").strip()
        except urllib.error.HTTPError as e:
            print(f"[DeepSeek] HTTP Error {e.code}: {e.read().decode('utf-8', errors='ignore')}")
        except Exception as e:
            print(f"[DeepSeek] Erro de conexão/timeout: {e}")

        return None


deepseek_service = DeepSeekService()
