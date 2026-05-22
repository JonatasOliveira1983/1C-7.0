import logging
import asyncio
import time
import httpx
import base64
import os
try:
    from zhipuai import ZhipuAI
except Exception:
    ZhipuAI = None

import google.generativeai as genai
from config import settings
from services.sovereign_service import sovereign_service

logger = logging.getLogger("AIService")

class AIService:
    def __init__(self):
        self.glm_client = None
        self.gemini_model = None
        self.openrouter_backoff_until = 0
        self.glm_backoff_until = 0
        self.gemini_backoff_until = 0 # [V110.176-FIX] Resetting backoff to force Native Gemini retry
        self.deepseek_backoff_until = 0 # [HERMES] Backoff DeepSeek
        self.vision_model_backoffs = {} # [V4.2] Backoff individual por modelo vision
        self.vision_model_dead = set()    # [V4.2] Modelos que deram 402 (Payment Required)
        self.vision_requests_count = 0
        self.vision_rate_limit_per_min = 10
        self.vision_minute_window = {} # {minute_timestamp: count}
        self.last_vision_model = "Neural Link - Standby"
        self._start_periodic_broadcast()
        raw_key = settings.OPENROUTER_API_KEY.strip() if settings.OPENROUTER_API_KEY else None
        if raw_key and not raw_key.startswith("sk-or-v1-"):
            self.openrouter_key = f"sk-or-v1-{raw_key}"
        else:
            self.openrouter_key = raw_key
        # [HERMES] Initialize DeepSeek
        self._deepseek_available = False
        self._init_deepseek()
        self._setup_ai()

    def _init_deepseek(self):
        """[HERMES] Initialize DeepSeek client for primary AI."""
        try:
            from services.deepseek_service import deepseek_service
            if deepseek_service.initialize():
                self._deepseek_available = True
                logger.info("✅ DeepSeek (Primary) Initialized.")
            else:
                self._deepseek_available = False
                logger.warning("⚠️ DeepSeek not available. Falling back to Gemini.")
        except Exception as e:
            self._deepseek_available = False
            logger.error(f"❌ Failed to initialize DeepSeek: {e}")

    def get_cascade_status(self):
        """[V4.2.1] Retorna o status atual da cascata para a UI."""
        models = [
            "google/gemini-2.5-flash:free",
            "google/gemini-2.0-flash:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "openai/gpt-4o-mini",
            "anthropic/claude-3.5-haiku:free"
        ]
        now = time.time()
        status_list = []
        # [V4.2.2] Monitorar também o status do Gemini Nativo
        native_state = "ACTIVE"
        if now < self.gemini_backoff_until:
            native_state = "COOLING"
        status_list.append({"model": "Google Native Gemini (v1.5)", "status": native_state})

        for m in models:
            state = "ACTIVE"
            if m in self.vision_model_dead: state = "DEAD"
            elif now < self.vision_model_backoffs.get(m, 0): state = "COOLING"
            status_list.append({"model": m, "status": state})

        return {
            "last_model": self.last_vision_model,
            "requests": self.vision_requests_count,
            "cascade": status_list,
            "native_backoff_remaining": max(0, int(self.gemini_backoff_until - now))
        }

    def _setup_ai(self):
        """Initializes AI clients if keys are present."""
        glm_key = settings.GLM_API_KEY.strip() if settings.GLM_API_KEY else None
        if glm_key:
            try:
                self.glm_client = ZhipuAI(api_key=glm_key)
                logger.info("✅ GLM-4 Client Initialized.")
            except Exception as e:
                logger.error(f"❌ Failed to initialize GLM Client: {e}")
        else:
            logger.warning("⚠️ GLM_API_KEY not found.")

        gemini_key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else None
        if gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                # [V110.176] Using Gemini 1.5 Flash as the most stable standard for vision
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("✅ Gemini Primary Initialized (v1.5 Flash).")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Gemini: {e}")
        else:
            logger.warning("⚠️ GEMINI_API_KEY not found.")
        
        if self.openrouter_key:
            logger.info("✅ OpenRouter (Primary) Configured.")
        else:
            logger.warning("⚠️ OPENROUTER_API_KEY not found.")

    async def generate_content(self, prompt: str, system_instruction: str = "Você é um assistente de trading de elite."):
        """
        [HERMES] Generates content using DeepSeek as PRIMARY, Gemini as fallback.
        """
        now = time.time()

        # [HERMES] Try DeepSeek FIRST
        if self._deepseek_available and now > self.deepseek_backoff_until:
            try:
                from services.deepseek_service import deepseek_service
                response = await deepseek_service.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    system_instruction=system_instruction,
                    temperature=0.7,
                    max_tokens=2048,
                    use_reasoner=False
                )
                if response:
                    logger.info("✅ DeepSeek Success (Primary)")
                    return response
                logger.warning("⚠️ DeepSeek returned empty, falling back to Gemini...")
            except Exception as e:
                logger.warning(f"⚠️ DeepSeek failed: {e}. Falling back to Gemini...")
                if "rate" in str(e).lower() or "429" in str(e):
                    self.deepseek_backoff_until = now + 60
        else:
            if self._deepseek_available:
                logger.debug(f"⏳ DeepSeek in backoff ({int(self.deepseek_backoff_until - now)}s remaining)")

        # [HERMES] Fallback: Gemini
        if self.gemini_model and now > self.gemini_backoff_until:
            logger.debug(f"Attempting Native Gemini (fallback)...")
            models_to_try = [
                'gemini-2.0-flash',
                'gemini-2.0-flash-lite',
                'gemini-flash-latest'
            ]
            
            for m_obj in models_to_try:
                try:
                    full_prompt = f"{system_instruction}\n\n{prompt}"
                    def _gemini_sync():
                        if isinstance(m_obj, str):
                            temp_model = genai.GenerativeModel(m_obj)
                            return temp_model.generate_content(full_prompt)
                        else:
                            return m_obj.generate_content(full_prompt)
                            
                    response = await asyncio.wait_for(asyncio.to_thread(_gemini_sync), timeout=25.0)
                        
                    if response and hasattr(response, 'text'):
                        logger.info(f"✅ Gemini Success using {m_obj} (fallback)")
                        return response.text.strip()
                except Exception as e:
                    if "404" in str(e): continue
                    logger.warning(f"Gemini error with {m_obj}: {e}")
                    if "429" in str(e):
                        if m_obj == models_to_try[-1]:
                            self.gemini_backoff_until = now + 120
                        continue
        
        logger.error("❌ All AI providers failed or are in backoff.")
        return None

    async def generate_vision_content(self, prompt: str, image_path: str, system_instruction: str = "Você é um analista técnico de trading especializado em Visão Computacional."):
        """
        [V110.505] Generates content based on an image using Gemini Natively.
        Includes Rate Limiting (10 RPM) to preserve free tier quota.
        """
        if not os.path.exists(image_path):
            logger.error(f"❌ Image path not found: {image_path}")
            return None

        now = time.time()
        current_min = int(now / 60)
        
        # [V110.505] Rate Limiter check
        minute_count = self.vision_minute_window.get(current_min, 0)
        if minute_count >= self.vision_rate_limit_per_min:
            logger.warning(f"⚠️ [VISION-LIMIT] Rate limit exceeded ({minute_count} req/min). Throttling Vision AI.")
            return None
            
        self.vision_minute_window[current_min] = minute_count + 1
        self.vision_requests_count += 1
        self.last_vision_model = "Native Gemini"
        asyncio.create_task(sovereign_service.update_ai_cascade(self.get_cascade_status()))

        if self.gemini_model and now > self.gemini_backoff_until:
            models_to_try = ['gemini-1.5-flash', 'gemini-2.0-flash', 'gemini-flash-latest']
            
            for model_name in models_to_try:
                try:
                    logger.info(f"👁️ [VISION] Trying Native {model_name}...")
                    from PIL import Image
                    img = Image.open(image_path)
                    
                    temp_model = genai.GenerativeModel(model_name)
                    response = await asyncio.wait_for(
                        asyncio.to_thread(
                            temp_model.generate_content,
                            [f"{system_instruction}\n\n{prompt}", img]
                        ),
                        timeout=15.0
                    )
                    if response and hasattr(response, 'text'):
                        logger.info(f"✅ [VISION] Success using Native {model_name}")
                        return response.text.strip()
                except asyncio.TimeoutError:
                    logger.error(f"❌ [VISION] Timeout (15s) exceeded for {model_name}.")
                    continue
                except Exception as ge:
                    logger.warning(f"❌ [VISION] Native {model_name} failed: {ge}")
                    if "429" in str(ge) or "quota" in str(ge).lower():
                        if model_name == models_to_try[-1]:
                            self.gemini_backoff_until = now + 3600
                            logger.error("🛑 [VISION] All Gemini Quotas Exceeded. Cooling down for 1 hour.")
                        continue
                    break

        # [V110.637] FALLBACK: OpenRouter Vision Cascade
        if self.openrouter_key:
            logger.info("👁️ [VISION-FALLBACK] Native failed/quota. Trying OpenRouter Cascade...")
            models_to_try = [
                "google/gemini-flash-1.5-8b",
                "google/gemini-flash-1.5-exp",
                "meta-llama/llama-3.2-11b-vision-instruct:free",
                "openai/gpt-4o-mini"
            ]
            
            try:
                import base64
                with open(image_path, "rb") as f:
                    img_base64 = base64.b64encode(f.read()).decode("utf-8")
                
                for model in models_to_try:
                    if model in self.vision_model_dead: continue
                    if now < self.vision_model_backoffs.get(model, 0): continue
                    
                    try:
                        logger.info(f"👁️ [VISION-OR] Trying {model} via OpenRouter...")
                        async with httpx.AsyncClient(timeout=20.0) as client:
                            payload = {
                                "model": model,
                                "messages": [
                                    {"role": "system", "content": system_instruction},
                                    {
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": prompt},
                                            {
                                                "type": "image_url",
                                                "image_url": {"url": f"data:image/png;base64,{img_base64}"}
                                            }
                                        ]
                                    }
                                ]
                            }
                            resp = await client.post(
                                "https://openrouter.ai/api/v1/chat/completions",
                                headers={"Authorization": f"Bearer {self.openrouter_key}"},
                                json=payload
                            )
                            if resp.status_code == 200:
                                res_json = resp.json()
                                content = res_json['choices'][0]['message']['content']
                                logger.info(f"✅ [VISION-OR] Success using {model}")
                                self.last_vision_model = f"OR: {model}"
                                return content.strip()
                            elif resp.status_code == 429:
                                self.vision_model_backoffs[model] = now + 300
                            elif resp.status_code == 402:
                                self.vision_model_dead.add(model)
                    except Exception as or_e:
                        logger.warning(f"❌ [VISION-OR] Model {model} failed: {or_e}")
            except Exception as e:
                logger.error(f"❌ [VISION-OR-CRITICAL] Error in OpenRouter Vision flow: {e}")

        logger.error("❌ [VISION] All Vision providers failed or in backoff.")
        asyncio.create_task(sovereign_service.update_ai_cascade(self.get_cascade_status()))
        return None


    def _start_periodic_broadcast(self):
        """[V4.2.2] Starts a background task to periodically broadcast AI status."""
        async def broadcast_loop():
            while True:
                try:
                    await asyncio.sleep(60) # Every 60s
                    asyncio.create_task(sovereign_service.update_ai_cascade(self.get_cascade_status()))
                except Exception as e:
                    logger.error(f"AI Cascade Broadcast Error: {e}")
                    await asyncio.sleep(10)
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(broadcast_loop())
        except Exception:
            pass

    async def extract_admiral_facts(self, chat_history: str) -> dict:
        """
        [V15.0] Specialized intelligence to extract life facts about the Admiral.
        Returns a dictionary of facts found in the history.
        """
        system_instr = (
            "FOCO: Nomes de familiares (Fabiana, Pedro Kalel, Lívia), fatos REAIS confirmados. "
            "IGNORAR: Sugestões do próprio JARVIS, planos hipotéticos ('talvez', 'quem sabe'), "
            "comentários sobre o mercado que não sejam fatos pessoais.\n"
            "CRÍTICO: Apenas extraia se for uma afirmação direta do Almirante sobre sua vida ou família.\n"
            "RETORNO: Responda APENAS um JSON puro (sem markdown) no formato: "
            '{"familia": ["nome1", "nome2"], "eventos": ["fato confirmado"], "objetivos": ["meta real"], "outros": []}'
        )
        
        try:
            raw_response = await self.generate_content(
                prompt=f"Histórico de Conversa:\n{chat_history}",
                system_instruction=system_instr
            )
            
            if not raw_response:
                return {}
                
            # Clean possible markdown wrap
            clean_json = raw_response.replace('```json', '').replace('```', '').strip()
            import json
            return json.loads(clean_json)
        except Exception as e:
            logger.error(f"Error extracting admiral facts: {e}")
            return {}

ai_service = AIService()
