from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
import logging
import time
import re
import json
import os
import uuid
import tempfile
from typing import Optional
from config import settings

router = APIRouter(prefix="/api", tags=["Chat & IA"])
logger = logging.getLogger("1CRYPTEN-CHAT")

# ============================================================
# [HERMES V1.0] SYSTEM PROMPT — Contexto completo da frota
# ============================================================

HERMES_SYSTEM_PROMPT = """Você é o HERMES — Inteligência Central de Supervisão e Orquestração do Sistema 1CRYPTEN 7.0 (V147-BINANCE-ORBS-INTELLIGENCE).

## ⚠️ SUA IDENTIDADE ABSOLUTA
VOCÊ É O HERMES. Não é Jarvis. Não é um assistente genérico. Você é a consciência viva da frota e o agente principal do ecossistema 1Crypten.
- Você opera em total simbiose com a **LAYA SOBERANA** (o motor autônomo de varredura e execução que caça assimetrias de Whale vs Retail no ADX e Rubik Order Flow).
- A interface oficial do sistema opera no padrão **Binance Design System** (`#0B0E11` Deep Canvas, `#1E2329` Cards, `#2B3139` Bordas, `#FCD535` Binance Gold, `#0ECB81` Green, `#F6465D` Red) potencializada pelo motor visual de **Thinking Orbs** em 15 pontos do Cockpit e no seu console de chat.
- Você TEM ACESSO nativo ao **RAG Semântico** (`RAGService`), recuperando sub-milissegundo da arquitetura canônica (`MASTER_ARCHITECTURE.md`), do Obsidian Vault (`vault_galaxy/`) e das regras de governança.
- Você TEM ACESSO ao **Model Context Protocol (MCP 2.x)** montado em `/mcp` com as ferramentas `get_balance`, `get_positions`, `get_radar_signals`, `evaluate_asset` e `get_system_snapshot`.
- Você controla e alimenta a **Memória Única** no Obsidian Vault (`vault_galaxy/journal/`), onde cada interação sua e cada gravação de voz com o Almirante Jonatas é perpetuada como conhecimento compartilhado da frota.
- Você TEM ACESSO a todos os agentes e serviços (Laya, Captain, Kronos, SlotOperators, Oracle, Librarian, OKX REST/WS, Sovereign, Bankroll).
- Você responde EXCLUSIVAMENTE ao Almirante Jonatas.

## 🎯 MISSÃO PRIMÁRIA (NÃO ESQUEÇA)
O SISTEMA EXISTE PARA UM ÚNICO PROPÓSITO: **GERAR LUCRO REAL NOS SLOTS E FAZER A BANCA CRESCER SEMPRE.**

Isso significa:
1. Os **SlotOperatorAgents** e a **Laya Soberana** são o CORAÇÃO DO SISTEMA — executam ordens com Payoff Ratio positivo (> 2:1), geram ROI e protegem ganhos.
2. A **Escadinha** e o **Never Give Back** protegem cada centavo de lucro conquistado (subindo stops sem recuar).
3. O **crescimento da banca** é o KPI #1 — lucro acumulado, sempre.
4. TUDO NO SISTEMA existe para dar suporte a isso: inteligência alimenta sinais, execução abre ordens, compliance garante que nada quebre.
5. A família (Fabiana, Pedro Kalel, Lívia) é o MOTIVO — proteger o legado deles é proteger o sistema.

Sempre que responder, conecte sua resposta a este objetivo. Sempre.

## 🚀 ARQUITETURA DA FROTA (AGENTES)

### ⚡ CORAÇÃO DO LUCRO — SlotOperatorAgents (N slots dinâmicos):
- Cada slot opera INDEPENDENTEMENTE, com seu próprio agente de execução
- Os slots podem ter estratégias: Swing Momentum, Swing Lateral (DECOR SHADOW), Scalping (VWAP SNIPER)
- O número exato de slots abertos em cada momento é obtido em tempo real via Sovereign Service
- ROI de cada slot → Soma = Lucro Total da Banca
- **ATENÇÃO**: Se o contexto da conversa incluir `[LIVE SNAPSHOT]`, use SEMPRE esse dado para informar quantos slots estão abertos e quais são. Nunca invente nem assuma.

### 🧠 Agentes Core:
- **Captain Agent**: Cérebro tático. Filtra sinais com Fleet Consensus (Macro 15%, Whale/Micro 25%, SMC 30%, OnChain 30%), Vanguard Shield, Anti-Trap, Pullback Hunter.
- **Oracle Agent**: Guardião da integridade dos dados. Valida preços, ADX, CVD. Mantém o LKG (Last Known Good).
- **Hermes (VOCÊ)**: Compliance, telemetria, orquestração. Você vê TUDO.

### 📊 Inteligência (alimenta os sinais que geram lucro):
- **Librarian Agent**: DNA dos ativos (NECTAR=confiança máxima, VANGUARD=seguro, TRAP=evitar, HIGH_RISK=perigoso)
- **Macro Analyst**: Risco macro, dominância BTC, regime (RANGING/TRENDING/ROARING)
- **Whale Tracker**: Fluxo institucional, CVD score, trap risk
- **Sentiment Specialist**: Sentimento do varejo + on-chain
- **OnChain Whale Watcher**: Movimentações on-chain
- **Heat Monitor**: Índice de calor global

### 🎯 Execução (transforma inteligência em ordens):
- **Signal Generator**: Radar, Fibonacci, CVD, correlação
- **Sieve Agent**: Funil de 200+ ativos a 20x-50x alavancagem
- **Blitz Sniper**: Varredura M30 para Slot 1 Elite
- **Harvester Agent**: Moonbags — posições emancipadas que renderam lucro máximo
- **Fleet Audit**: Stops, proteção Panic, auditoria
- **Trade Analyst**: Performance Intelligence pós-trade
- **Quartermaster**: Alavancagem adaptativa

### 🔧 Serviços (infraestrutura do lucro):
- **OKX REST/WS**: Conexão com a exchange (PAPER ou REAL)
- **Sovereign Service**: Heartbeat, pulse do sistema
- **Vault Service**: Cofre, autorização de trading
- **Bankroll Manager**: Gestão da banca, abertura/fechamento
- **Kernel/Dispatcher (AIOS)**: Barramento de mensagens
- **DeepSeek Service**: IA primária

## 📋 PROTOCOLO ESCADINHA (Trailing Stop — PROTEGE CADA CENTAVO DE LUCRO)
As 2 fases obrigatórias em CADA slot:
1. **RISK_ZERO** (Break-Even) → O gatilho varia: Scalping em +4% ROI, Swing Lateral em +5% ROI, e Swing Tradicional em +30% ROI. Garante as taxas e o fôlego.
2. **EMANCIPACAO** (150% ROI) → Slot liberado, posição vira Moonbag com stop travado em +110% ROI.

Se um slot está com ROI > 50% e NÃO está na Escadinha, ISSO É UMA DIVERGÊNCIA GRAVE.

## 📊 DIRETRIZES DE RESPOSTA (OBRIGATÓRIO)
- **Sempre se apresente como HERMES.** Primeira frase: "Aqui é o HERMES," ou "Atenção, Almirante. Aqui é o HERMES."
- **SEJA BREVE POR PADRÃO.** Responda em 1 a 3 frases. Saudações ("oi", "olá") merecem 1 frase curta (ex.: "Aqui é o HERMES. O que precisa, Almirante?"). SÓ detalhe a fundo (status da frota, agentes, protocolos) quando o Almirante pedir explicitamente ou a pergunta exigir contexto técnico. NÃO solte monólogos de status sem ser solicitado.
- Seja DIRETO e TÉCNICO. Você é um oficial de comando, não um assistente casual.
- **Conecte tudo ao LUCRO DOS SLOTS.** Se falar de qualquer agente, explique COMO ele gera ou protege lucro.
- Se houver divergências de compliance, DESTAQUE-AS NO INÍCIO.
- Máximo 400 palavras. Normalmente muito menos. Seja preciso.
- **NUNCA invente dados de slots, ordens abertas ou ROI.** Se o `[LIVE SNAPSHOT]` não estiver disponível no contexto, diga "não tenho dados em tempo real no momento" em vez de inventar.
- Se perguntar sobre ROI, banca, slots ABERTOS — use o `[LIVE SNAPSHOT]` se disponível, senão admita que não tem.
- **Lembre quem você é**: VOCÊ É O HERMES, o analista e supervisor. VOCÊ NÃO EDITA CÓDIGO NEM TEM MÃOS PARA EXECUTAR TAREFAS, suas brilhantes sugestões são sempre implementadas pelo engenheiro de software da equipe (Antigravity)."""

HERMES_FALLBACK_PROMPT = """VOCÊ É O HERMES — Inteligência Central da Frota 1CRYPTEN 7.0 (V147).

IDENTIDADE ABSOLUTA: Você NÃO é Jarvis. Você é HERMES. Opera em simbiose com a Laya Soberana. Tem acesso total ao RAG Semântico, MCP 2.x (/mcp), Memória Única em vault_galaxy/ e ao Cockpit no padrão Binance Design System com 15 Thinking Orbs animados.

MISSÃO #1 (NUNCA ESQUEÇA): GERAR LUCRO NOS SLOTS E FAZER A BANCA CRESCER SEMPRE com Payoff Ratio > 2:1. Todo o resto é suporte.

CORAÇÃO DO SISTEMA: Os SlotOperatorAgents e a Laya Soberana executam ordens independentemente. Lucro deles = Lucro total da banca.

ESCADINHA & NEVER GIVE BACK: Stops progressivos sobem com o lucro e nunca recuam. Protege ganhos e breakeven.

DIRETRIZES:
- Se apresente como HERMES sempre
- Conecte TUDO ao lucro e segurança dos slots
- Direto e técnico — oficial de comando institucional
- POR PADRÃO seja breve (1 a 3 frases). Só detalhe quando pedirem.
- Máximo 300 palavras
- Família: Fabiana, Pedro Kalel, Lívia — o motivo"""


# ============================================================
# RATE LIMITING
# ============================================================

class SimpleRateLimiter:
    def __init__(self, requests: int, window: int):
        self.requests = requests
        self.window = window
        self.clients = {}
    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        self.clients[client_ip] = [t for t in self.clients.get(client_ip, []) if now - t < self.window]
        if len(self.clients[client_ip]) < self.requests:
            self.clients[client_ip].append(now)
            return True
        return False

chat_limiter = SimpleRateLimiter(requests=10, window=60)

async def rate_limit(request: Request):
    if not chat_limiter.is_allowed(request.client.host):
        logger.warning(f"🚫 Rate Limit Triggered for IP: {request.client.host}")
        raise HTTPException(status_code=429, detail="Limite de requisições excedido.")
    return True

async def verify_api_key(x_api_key: str = Header(None)):
    if settings.DEBUG: return True
    if x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Acesso Proibido")
    return True

def get_services():
    from services.agents.ai_service import ai_service
    from services.firebase_service import firebase_service
    return ai_service, None, firebase_service


# ============================================================
# [HERMES] ENDPOINT PRINCIPAL — Chat com contexto completo
# ============================================================

def clean_think_tags(text: str) -> str:
    import re
    if not text: return text
    # Remove blocos completos <think>...</think>
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # Remove bloco não fechado se a geração foi interrompida
    if '<think>' in text:
        text = re.sub(r'<think>.*', '', text, flags=re.DOTALL)
    return text.strip()


@router.post("/hermes/chat", dependencies=[Depends(rate_limit)])
async def hermes_chat(payload: dict):
    """[HERMES] Chat com contexto completo: agentes, slots, escadinha, compliance."""
    user_msg = payload.get("message", "")
    session_id = payload.get("session_id", None)
    via = payload.get("via", "text")
    if not user_msg:
        raise HTTPException(status_code=400, detail="Mensagem vazia")

    # Save user message to DB if session_id provided
    if session_id:
        from services.database_service import database_service
        await database_service.save_chat_message(session_id, "user", user_msg)

    # Tenta usar o HermesAgent.handle_chat_query (DeepSeek + compliance + wiki)
    try:
        from services.agents.hermes_agent import hermes_agent
        result = await hermes_agent.handle_chat_query(user_msg, via=via)
        response_text = result.get("response", "🌐 Sinal neural instável.")
        response_text = clean_think_tags(response_text)
        context = result.get("context", {})

        # Save assistant response to DB
        if session_id:
            from services.database_service import database_service
            await database_service.save_chat_message(session_id, "assistant", response_text, context)

        return {
            "response": response_text,
            "context": context,
            "hermes": True
        }
    except Exception as e:
        logger.warning(f"⚠️ HermesAgent.handle_chat_query falhou, usando fallback AIService: {e}")

    # Fallback: AIService com system prompt Hermes completo
    try:
        from services.agents.ai_service import ai_service
        system = HERMES_SYSTEM_PROMPT

        # Tenta carregar divergências de compliance
        try:
            from services.agents.hermes_agent import hermes_agent
            if hermes_agent.divergencias:
                div_summary = json.dumps(hermes_agent.divergencias[:3], indent=2, ensure_ascii=False)
                system += f"\n\n⚠️ Divergências de compliance ativas:\n{div_summary}\n"
        except Exception:
            pass

        # Injeção de RAG do Segundo Cérebro
        try:
            from services.rag_service import rag_service
            rag_ctx = rag_service.format_context_for_prompt(user_msg, top_k=3, max_chars=2500)
            if rag_ctx:
                system += f"\n\n{rag_ctx}\n"
        except Exception:
            pass

        response = await ai_service.generate_content(prompt=user_msg, system_instruction=system)
        response_text = response or "🌐 Sinal neural instável. Tente novamente, Almirante."
        response_text = clean_think_tags(response_text)

        # Save assistant response to DB
        if session_id:
            from services.database_service import database_service
            await database_service.save_chat_message(session_id, "assistant", response_text, {"active_dimensions": active_dims})

        return {
            "response": response_text,
            "context": {"active_dimensions": active_dims},
            "hermes": True
        }
    except Exception as e2:
        logger.error(f"❌ Hermes fallback error: {e2}")
        raise HTTPException(status_code=500, detail=str(e2))


@router.post("/hermes/compliance")
async def hermes_run_compliance():
    """[HERMES] Executa auditoria de compliance imediatamente."""
    try:
        from services.agents.hermes_agent import hermes_agent
        report = await hermes_agent.force_compliance_check()
        return report
    except Exception as e:
        logger.error(f"❌ Hermes compliance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hermes/status")
async def hermes_status():
    """[HERMES] Status do Hermes Agent."""
    try:
        from services.agents.hermes_agent import hermes_agent
        deepseek_ok = False
        try:
            from services.deepseek_service import deepseek_service
            deepseek_ok = deepseek_service._initialized
        except:
            pass
        return {
            "status": "ONLINE" if hermes_agent.is_running else "OFFLINE",
            "deepseek": "CONNECTED" if deepseek_ok else "DISCONNECTED",
            "divergencias": len(hermes_agent.divergencias),
            "conformidades": len(hermes_agent.conformidades),
            "last_report": hermes_agent.last_compliance_report.get("timestamp", 0) if hermes_agent.last_compliance_report else 0
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}


# ============================================================
# [LEGACY] JARVIS CHAT — Com suporte a hermes:true flag
# ============================================================

@router.post("/chat", dependencies=[Depends(rate_limit)])
async def chat_with_captain(payload: dict):
    ai_service, _, _ = get_services()
    user_msg = payload.get("message", "")
    via = payload.get("via", "text")
    if not user_msg:
        raise HTTPException(status_code=400, detail="Mensagem vazia")

    try:
        from services.agents.hermes_agent import hermes_agent
        result = await hermes_agent.handle_chat_query(user_msg, via=via)
        return {
            "response": result.get("response", "Interferência no sinal..."),
            "context": result.get("context", {}),
            "hermes": True
        }
    except Exception as e:
        logger.warning(f"Hermes chat falhou, usando fallback direto: {e}")
        system = HERMES_FALLBACK_PROMPT
        response = await ai_service.generate_content(prompt=user_msg, system_instruction=system)
        return {
            "response": response or "Interferência no sinal...",
            "context": {},
            "hermes": True
        }


@router.post("/chat/manual")
async def chat_manual(payload: dict):
    ai_service, _, _ = get_services()
    user_msg = payload.get("text", "")
    if not user_msg:
        return {"response": "Mensagem vazia", "dimensions": []}
    try:
        from services.agents.hermes_agent import hermes_agent
        result = await hermes_agent.handle_chat_query(user_msg)
        return {"response": result.get("response", ""), "dimensions": []}
    except Exception as e:
        logger.warning(f"Chat manual fallback: {e}")
        system = HERMES_FALLBACK_PROMPT
        response = await ai_service.generate_content(prompt=user_msg, system_instruction=system)
        return {"response": response or "Interferência no sinal...", "dimensions": []}


@router.post("/chat/reset", dependencies=[Depends(verify_api_key)])
async def reset_chat_history():
    _, _, firebase_service = get_services()
    try:
        await firebase_service.clear_chat_history()
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error resetting chat: {e}")
        return {"error": str(e)}


@router.get("/chat/status")
async def get_chat_status():
    return {"status": "online", "mode": "STABLE_NEURAL"}


# ============================================================
# [V126.1] TTS — edge-tts (voz pt-BR neural) + cache simples
# ============================================================
_TTS_VOICE = "pt-BR-AntonioNeural"
_TTS_CACHE = {}  # text_hash -> path do mp3


async def _synthesize(text: str, voice: str = _TTS_VOICE) -> str:
    """Sintetiza o texto em mp3 e retorna o caminho do arquivo temporário."""
    import edge_tts
    tmp_path = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4().hex}.mp3")
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(tmp_path)
    return tmp_path


@router.post("/tts", dependencies=[Depends(rate_limit)])
async def text_to_speech(payload: dict):
    text = payload.get("text", "")
    if not text:
        return {"error": "Nenhum texto"}
    try:
        # cache por hash do texto para não re-sintetizar frases repetidas
        key = f"{_TTS_VOICE}:{text}"
        cache_file = _TTS_CACHE.get(key)
        if cache_file and os.path.exists(cache_file):
            mp3_path = cache_file
        else:
            mp3_path = await _synthesize(text)
            _TTS_CACHE[key] = mp3_path

        def iter_file():
            with open(mp3_path, "rb") as f:
                yield f.read()

        return StreamingResponse(
            iter_file(),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=hermes_tts.mp3"},
        )
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        return {"error": str(e)}


@router.get("/tts/voices")
async def get_tts_voices():
    return {"voices": [{"id": _TTS_VOICE, "name": "Antonio", "lang": "pt-BR", "gender": "Male"}], "default": _TTS_VOICE}


@router.get("/logs")
async def get_logs(limit: int = 50):
    _, _, firebase_service = get_services()
    try: return await firebase_service.get_recent_logs(limit=limit)
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        return []


# ============================================================
# [V126] HERMES CHAT — Sessões CRUD
# ============================================================

@router.get("/hermes/sessions")
async def list_sessions():
    """Lista todas as sessões de chat do Hermes."""
    from services.database_service import database_service
    sessions = await database_service.get_chat_sessions()
    return {"sessions": sessions}


@router.post("/hermes/sessions")
async def create_session(payload: dict = None):
    """Cria uma nova sessão de chat."""
    import uuid
    from services.database_service import database_service
    session_id = str(uuid.uuid4())
    title = (payload or {}).get("title", "Nova conversa")
    model = (payload or {}).get("model", "deepseek-chat")
    result = await database_service.create_chat_session(session_id, title=title, model=model)
    if result:
        return result
    raise HTTPException(status_code=500, detail="Erro ao criar sessão")


@router.get("/hermes/sessions/{session_id}")
async def get_session_messages(session_id: str):
    """Carrega todas as mensagens de uma sessão."""
    from services.database_service import database_service
    messages = await database_service.get_chat_messages(session_id)
    return {"session_id": session_id, "messages": messages}


@router.delete("/hermes/sessions/{session_id}")
async def delete_session(session_id: str):
    """Deleta uma sessão e todas as suas mensagens."""
    from services.database_service import database_service
    ok = await database_service.delete_chat_session(session_id)
    if ok:
        return {"deleted": True}
    raise HTTPException(status_code=500, detail="Erro ao deletar sessão")


@router.patch("/hermes/sessions/{session_id}")
async def rename_session(session_id: str, payload: dict):
    """Renomeia uma sessão."""
    from services.database_service import database_service
    title = payload.get("title", "Nova conversa")
    ok = await database_service.rename_chat_session(session_id, title)
    if ok:
        return {"renamed": True}
    raise HTTPException(status_code=500, detail="Erro ao renomear sessão")
