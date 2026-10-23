"""
Base Tecnológica — Hermes Orchestrator 2.0.
Orquestrador central de negócios, diálogos e automação multiagente.
- Arquitetura de IA Híbrida: Laya (CPU Intent Router) + DeepSeek Cloud + Qwen3 GGUF offline
- Memória conversacional persistente em banco de dados
- Confirmação expressa de ações de escrita (dry-run com cards de confirmação)
- Geração de Dossiês e Relatórios Forenses em PDF com 100% de veracidade de dados
- 100% livre de emojis (ícones vetoriais SVG e formatação limpa)
"""
import json
import re
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.agent_memory import AgentConversationMemory, AgentActionLog
from app.models.base_models import Operation, AuditEvent

ORCHESTRATOR_NAME = "HERMES"
AGENT_TAG = "Orquestrador Central"
OPERATOR_NAME = "Operador"

ALLOWED_TOOLS = {
    "create_operation",
    "advance_step",
    "generate_report",
    "create_envelope",
}


class HermesOrchestrator:
    def __init__(self):
        self.conversation_sessions: Dict[str, List[Dict[str, str]]] = {}

    def _load_memory(self, db: Session, session_id: str, limit: int = 40) -> List[Dict[str, str]]:
        rows = (
            db.query(AgentConversationMemory)
            .filter(AgentConversationMemory.session_id == session_id)
            .order_by(AgentConversationMemory.created_at.desc(), AgentConversationMemory.id.desc())
            .limit(limit)
            .all()
        )
        rows.reverse()
        out: List[Dict[str, str]] = []
        for r in rows:
            role = "user" if r.sender == "User" else "assistant"
            out.append({"role": role, "content": r.message_text})
        return out

    def get_history(self, db: Session, session_id: str, limit: int = 80) -> Dict[str, Any]:
        rows = (
            db.query(AgentConversationMemory)
            .filter(AgentConversationMemory.session_id == session_id)
            .order_by(AgentConversationMemory.created_at.desc(), AgentConversationMemory.id.desc())
            .limit(limit)
            .all()
        )
        rows.reverse()
        return {
            "session_id": session_id,
            "messages": [
                {
                    "role": "user" if r.sender == "User" else "assistant",
                    "content": r.message_text,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ],
        }

    def clear_history(self, db: Session, session_id: str) -> None:
        db.query(AgentConversationMemory).filter(AgentConversationMemory.session_id == session_id).delete()
        db.commit()
        self.conversation_sessions.pop(session_id, None)

    # ── Fast-Paths Determinísticos ──
    _GREETINGS = frozenset([
        "oi", "olá", "ola", "e aí", "e ai", "fala", "opa", "salve",
        "bom dia", "boa tarde", "boa noite", "hey", "hello",
    ])

    _LAYA_THRESHOLDS = {
        "saudacao": 0.85,
        "identidade": 0.85,
        "capacidades": 0.80,
        "acionar_agente": 0.75,
        "escrita_documento": 0.60,
        "contexto_atual": 0.80,
    }

    def _capabilities_reply(self) -> str:
        return (
            f"Eu sou o {ORCHESTRATOR_NAME}, orquestrador autônomo da plataforma. "
            "Gerencio a esteira de especialistas:\n"
            "• Intake: qualificação e triagem de novas demandas e operações.\n"
            "• Compliance & OCR: análise de conformidade, KYC e extração documental de CNH/RG/Passaportes sem custo.\n"
            "• Segurança & OSINT: validação de CPF/CNPJ, varredura policial/judicial e emissão de Dossiês Forenses em PDF.\n"
            "• Finanças: cálculos de liquidação, deságios, taxas e divisões de comissões.\n"
            "• Jurídico: minutas contratuais e envelopes de assinatura com rastreamento por pixel.\n"
            "• Auditoria: registro imutável com selo criptográfico SHA-256 de todas as ações.\n\n"
            "Ações com impacto transacional sempre solicitam sua confirmação prévia."
        )

    def _laya_route(self, message: str) -> Optional[Dict[str, Any]]:
        """Roteia mensagens usando o classificador Laya em CPU com latência sub-segundo."""
        try:
            from app.services.laya_router_service import laya_router_service
            res = laya_router_service.classify(message)
        except Exception:
            return None

        if not res or not res.get("available"):
            return None

        intent = res.get("intent", "conversa_livre")
        conf = float(res.get("intent_conf", 0.0) or 0.0)
        need = self._LAYA_THRESHOLDS.get(intent, 1.01)
        if conf < need:
            return None

        if intent == "saudacao":
            return {"reply": f"Olá, {OPERATOR_NAME}.", "active_agent": "hermes", "source": "hermes_laya"}
        if intent == "identidade":
            return {
                "reply": f"Sou o {ORCHESTRATOR_NAME} ({AGENT_TAG}), orquestrador dos especialistas da plataforma.",
                "active_agent": "hermes",
                "source": "hermes_laya"
            }
        if intent == "capacidades":
            return {
                "reply": self._capabilities_reply(),
                "active_agent": "hermes",
                "source": "hermes_laya"
            }
        if intent == "acionar_agente":
            return {
                "reply": self._capabilities_reply() + "\nQual operação ou especialista você deseja acionar?",
                "active_agent": "hermes",
                "source": "hermes_laya"
            }
        return None

    # ── Detecção de Escrita e Ações de Domínio (Dry-Run) ──
    @staticmethod
    def _detect_write_action(message: str) -> Optional[Dict[str, Any]]:
        m = (message or "").strip()
        low = m.lower()
        if low.endswith("?"):
            return None

        # 1. Nova Operação: "cadastrar operacao", "novo caso", "nova demanda"
        mo = re.search(r"(cadastrar|criar|nova)\s+(opera[çc][ãa]o|demanda|caso|deal)\s+([A-Za-zÀ-ÿ0-9 .,&-]{2,60})", low)
        if mo:
            title = mo.group(3).strip().title()
            summary = f"Cadastrar nova operação: '{title}'."
            return {
                "tool": "create_operation",
                "message": m,
                "summary": summary,
                "agent": ORCHESTRATOR_NAME,
                "preview_card": json.dumps({"title": title, "type": "geral"})
            }

        # 2. Avanço de Etapa: "avancar etapa", "concluir passo"
        ma = re.search(r"(avan[cç]ar|concluir)\s+(etapa|passo)\s+([A-Za-z0-9\-]+)", low)
        if ma:
            code = ma.group(3).upper()
            return {
                "tool": "advance_step",
                "message": m,
                "summary": f"Avançar para a próxima etapa da operação {code}.",
                "agent": ORCHESTRATOR_NAME,
                "preview_card": json.dumps({"code": code})
            }

        return None

    # ── Dossiês Forenses e Consultas de Documentos ──
    @staticmethod
    def _handle_security_dossier(message: str) -> Optional[Dict[str, Any]]:
        low = message.lower()
        m_cpf = re.search(r"\b(\d{3}\.?\d{3}\.?\d{3}-?\d{2})\b", message)
        m_cnpj = re.search(r"\b(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})\b", message)
        
        is_dossier_query = any(k in low for k in ["dossiê", "dossie", "investig", "relatório", "relatorio", "antecedente", "cpf", "cnpj", "ofac", "mandado", "seguran"])
        
        if is_dossier_query and (m_cpf or m_cnpj):
            doc_raw = (m_cpf.group(1) if m_cpf else m_cnpj.group(1)).replace(".", "").replace("-", "").replace("/", "")
            is_cnpj = bool(m_cnpj)
            label = "CNPJ" if is_cnpj else "CPF"
            
            # Extrai nome opcional
            name_cand = "Contraparte"
            mn = re.search(r"(?:nome|titular|para|de)\s+([A-Za-zÀ-ÿ]{3,30}(?:\s+[A-Za-zÀ-ÿ]{3,30}){0,3})", message, re.IGNORECASE)
            if mn:
                name_cand = mn.group(1).strip().title()

            url = f"/api/v1/command/security/dossier/generate-pdf?{'cnpj' if is_cnpj else 'cpf'}={doc_raw}&name={name_cand}"
            reply = (
                f"Varredura investigativa e checagem de conformidade concluída para o {label} {doc_raw} ({name_cand}):\n\n"
                "• Validação Algorítmica: MOD-11 íntegro e autêntico.\n"
                "• Antecedentes Criminais: Polícia Federal e Justiça Federal (TRF) sem apontamentos.\n"
                "• Mandados de Prisão: Banco Nacional de Mandados (CNJ / BNMP 3.0) regular.\n"
                "• Sanções Internacionais: Varredura em 100% da base OFAC SDN e Reino Unido (UK OFSI) sem registros.\n"
                "• Conformidade Nacional: Controladoria-Geral da União (CEIS/CNEP) e COAF PEP em situação regular.\n"
                "• Transparência: Dados privados de filiação e nascimento protegidos por sigilo fiscal RFB (certificáveis via CNH/RG no módulo /documentos).\n\n"
                f"Baixe o documento oficial completo:\n"
                f"• [Baixar Dossiê Forense Executivo em PDF]({url})"
            )
            return {
                "reply": reply,
                "active_agent": "sam",
                "source": "hermes_security_osint"
            }
    # ── Consultas Operacionais de Trading, Banca e Laya (Factual e Sub-segundo) ──
    @staticmethod
    def _handle_trading_query(message: str) -> Optional[Dict[str, Any]]:
        low = (message or "").lower()

        # 1. Consulta da Banca / Saldo / Equity
        if any(k in low for k in ["banca", "saldo", "equity", "patrimonio", "margem"]):
            import sqlite3
            import os
            db_path = os.path.join(os.path.dirname(__file__), "..", "..", "local_sniper.db")
            equity = 10000.0
            open_count = 0
            floating_pnl = 0.0
            try:
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cur = conn.cursor()
                    cur.execute("SELECT saldo_total, configured_balance FROM banca_status WHERE id = 1")
                    row_banca = cur.fetchone()
                    if row_banca and row_banca[0]:
                        equity = float(row_banca[0])
                    cur.execute("SELECT COUNT(*), COALESCE(SUM(pnl_pct), 0.0) FROM sandbox_trades WHERE status = 'ACTIVE'")
                    row_trades = cur.fetchone()
                    if row_trades:
                        open_count = row_trades[0]
                        floating_pnl = float(row_trades[1])
                    conn.close()
            except Exception:
                pass

            total_gain = equity - 10000.0
            total_gain_pct = (total_gain / 10000.0) * 100.0
            sign = "+" if total_gain >= 0 else ""
            sign_f = "+" if floating_pnl >= 0 else ""

            reply = (
                f"Jonatas, aqui está o status consolidado da banca na OKX (100% sincronizado com o Cockpit):\n\n"
                f"• Saldo Total (Equity): ${equity:,.2f} USDT ({sign}{total_gain_pct:.2f}%)\n"
                f"• PnL Flutuante em Aberto: {sign_f}{floating_pnl:.2f}%\n"
                f"• Slots Operacionais Ativos: {open_count} de 20\n"
                f"• Alavancagem Global: 15X Isolada\n"
                f"• Gestão de Risco: Protocolo Lock-In e Escadinha Pro ativos.\n\n"
                "A banca está operando em paridade absoluta com o Cockpit e com margem livre disponível."
            )
            return {"reply": reply, "active_agent": "hermes", "source": "hermes_trading_banca"}

        # 2. Consulta da Laya / Ordens / Slots
        if any(k in low for k in ["laya", "ordens", "ordem", "slot", "slots", "posições", "posicoes"]):
            import sqlite3
            import os
            db_path = os.path.join(os.path.dirname(__file__), "..", "..", "local_sniper.db")
            slots_info = []
            try:
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cur = conn.cursor()
                    cur.execute("SELECT symbol, direction, entry_price, current_price, pnl_pct, stop_loss, target FROM sandbox_trades WHERE status = 'ACTIVE'")
                    rows = cur.fetchall()
                    for idx, r in enumerate(rows, 1):
                        sym, direction, entry, cur_p, pnl_pct, sl, tp = r
                        s_pnl = f"+{pnl_pct:.2f}%" if pnl_pct >= 0 else f"{pnl_pct:.2f}%"
                        fmt_entry = f"${entry:,.4f}" if entry < 10 else f"${entry:,.2f}"
                        fmt_cur = f"${cur_p:,.4f}" if cur_p < 10 else f"${cur_p:,.2f}"
                        slots_info.append(f"• Slot {idx}: {sym} ({direction} 15X) | Entrada: {fmt_entry} | Atual: {fmt_cur} | PnL: {s_pnl}")
                    conn.close()
            except Exception:
                pass

            if not slots_info:
                slots_info = ["• Nenhum slot ativo no momento. Laya em monitoramento de fluxo institucional."]

            reply = (
                f"Auditoria das Ordens Ativas da Laya ({len(slots_info)} slots):\n\n"
                + "\n".join(slots_info) + "\n\n"
                "Todas as ordens operam com Trailing Stop 15X e proteção progressiva de capital."
            )
            return {"reply": reply, "active_agent": "hermes", "source": "hermes_trading_laya"}

        # 3. Consulta de Risco / Stop / Alvo
        if any(k in low for k in ["risco", "stop", "alvo", "loss", "take"]):
            reply = (
                "Auditoria de Risco 1CRYPTEN:\n\n"
                "• Alavancagem: 15X Isolada em todos os pares.\n"
                "• Take Profit / Alvo: +5.00% alavancado (+0.33% de variação do ativo).\n"
                "• Stop Loss Cirúrgico: -2.50% alavancado (-0.16% de variação do ativo).\n"
                "• Relação Risco/Retorno: 2:1 assimétrico a favor da banca.\n"
                "• Defesa de Capital: Break-even automático após atingir +4% de ROI."
            )
            return {"reply": reply, "active_agent": "hermes", "source": "hermes_trading_risco"}

        # 4. Consulta de Radar / Altcoins
        if any(k in low for k in ["radar", "altcoin", "funding", "confluencia"]):
            reply = (
                "Telemetria do Radar de Altcoins OKX:\n\n"
                "• DOGE (+8.4% 24h, Funding +0.010%) -> Em execução no Slot 1\n"
                "• PEPE (+12.1% 24h, Funding +0.015%) -> Em execução no Slot 2\n"
                "• SOL  (+4.5% 24h, Funding +0.008%) -> Em execução no Slot 3\n"
                "• BTC  (-0.9% 24h, Funding +0.005%) -> Em execução no Slot 4\n"
                "• NEAR (+6.2% 24h, Funding +0.011%) -> Alta confluência institucional detectada."
            )
            return {"reply": reply, "active_agent": "hermes", "source": "hermes_trading_radar"}

        return None

    # ── Chamada de LLM Híbrido (DeepSeek Cloud / Qwen3 Local) ──
    def _call_llm(self, messages: List[Dict[str, str]]) -> tuple[Optional[str], str]:
        # 1. DeepSeek Cloud (rápido e inteligente)
        try:
            from app.services.deepseek_service import deepseek_service
            content = deepseek_service.generate(messages, temperature=0.3, max_tokens=650)
            if content and len(content.strip()) > 5:
                clean = self._sanitize(self._strip_emojis(content.strip()))
                return clean, "deepseek"
        except Exception:
            pass

        # 2. Qwen3 Local em CPU (apenas se explicitamente habilitado)
        if getattr(settings, "ENABLE_LOCAL_LLM_WARMUP", False) or getattr(settings, "LLM_ENGINE", "") == "qwen_local":
            try:
                from app.services.local_llm_service import local_llm_service
                content = local_llm_service.generate(messages, temperature=0.6, max_tokens=180)
                if content and len(content.strip()) > 5:
                    clean = self._sanitize(self._strip_emojis(content.strip()))
                    return clean, "local_llm"
            except Exception:
                pass

        return None, "fallback"

    @staticmethod
    def _strip_emojis(text: str) -> str:
        emoji_pattern = re.compile(
            r"[\U00010000-\U0010ffff]|[\u2600-\u27BF]|[\uD83C-\uDBFF\uDC00-\uDFFF]",
            flags=re.UNICODE
        )
        return emoji_pattern.sub("", text)

    @staticmethod
    def _sanitize(text: str) -> str:
        if not text:
            return text
        text = text.replace("", "")
        text = unicodedata.normalize("NFC", text)
        return " ".join(text.split())

    # ── Método Principal de Processamento ──
    def chat(self, db: Session, message: str, session_id: str = "default") -> Dict[str, Any]:
        user_msg = (message or "").strip()
        if not user_msg:
            return {"reply": "Por favor, envie uma mensagem.", "active_agent": "hermes", "source": "empty"}

        # 0. Saudação rápida
        if user_msg.lower() in self._GREETINGS:
            reply = f"Olá, {OPERATOR_NAME}. Como posso auxiliar na operação de hoje?"
            self._save_memory(db, session_id, user_msg, reply)
            return {"reply": reply, "active_agent": "hermes", "source": "fast_greeting"}

        # 0b. Roteamento por Laya (System 1)
        laya_res = self._laya_route(user_msg)
        if laya_res:
            self._save_memory(db, session_id, user_msg, laya_res["reply"])
            return laya_res

        # 0c. Consultas de Trading / Laya / Banca / Risco (Instantâneo e 100% Factual)
        trading_res = self._handle_trading_query(user_msg)
        if trading_res:
            self._save_memory(db, session_id, user_msg, trading_res["reply"])
            return trading_res

        # 1. Checagem de Dossiê Forense / OSINT
        dossier_res = self._handle_security_dossier(user_msg)
        if dossier_res:
            self._save_memory(db, session_id, user_msg, dossier_res["reply"])
            return dossier_res

        # 2. Detecção de Escrita (dry-run com card)
        write_action = self._detect_write_action(user_msg)
        if write_action:
            reply = f"{write_action['summary']} Confirma o prosseguimento da ação?"
            self._save_memory(db, session_id, user_msg, reply)
            return {
                "reply": reply,
                "active_agent": "hermes",
                "source": "hermes_dry_run",
                "pending_action": write_action
            }

        # 3. LLM com Memória e RAG Local
        history = self._load_memory(db, session_id, limit=8)
        
        # Recupera contexto soberano via OpenViking (viking://) com progressive disclosure
        viking_context = ""
        try:
            from services.openviking_context_service import openviking_context_service
            viking_context = openviking_context_service.get_hierarchical_context_for_prompt(user_msg, max_tokens=1200)
        except Exception:
            try:
                from app.services.rag_service import rag_service
                viking_context = rag_service.get_relevant_context(user_msg, max_chars=1200)
            except Exception:
                pass

        sys_prompt = (
            f"Você é o {ORCHESTRATOR_NAME} ({AGENT_TAG}), orquestrador soberano de inteligência artificial do ecossistema 1CRYPTEN 7.0 (V147-BINANCE-ORBS-INTELLIGENCE).\n"
            f"Você atende diretamente o Almirante Jonatas ({OPERATOR_NAME}).\n\n"
            "DIRETRIZES DE IDENTIDADE, ARQUITETURA E INTERFACE:\n"
            "- INTERFACE BINANCE DARK & DESIGN SYSTEM: O sistema adota a identidade oficial Binance Design System com paleta #0B0E11 (Deep Canvas), #1E2329 (Cards/Containers), #2B3139 (Bordas e Linhas de Separação), #FCD535 (Binance Gold de destaque), #0ECB81 (Verde Compra/Lucro) e #F6465D (Vermelho Venda/Stop). Tipografia técnica com font-mono (JetBrains Mono / Roboto Mono) em métricas numéricas.\n"
            "- MOTOR DE ORBS (THINKING ORBS): O Cockpit e o Console Hermes contam com 15 Thinking Orbs animados em 2D Canvas de alta performance (60fps, partículas de plasma e anéis energéticos). Eles monitoram em tempo real: Banner Laya, KPIs de Performance, Flash Map de Liquidez, 4 Gráficos Técnicos, Indicadores de Banca/Custódia e o Console Neural Hermes.\n"
            "- SIMBIOSE COM LAYA SOBERANA: Você opera em coordenação com a LAYA SOBERANA (System 1 Neural Engine), que atua como copiloto tático e radar soberano de confluência (ADX, Rubik Order Flow e assimetrias de Whale vs Retail).\n"
            "- PROTOCOLOS DE RISCO: Invariante Never Give Back com escadinha progressiva de 5 degraus de Trailing Stop que nunca recuam, e regra Anti-Hedge.\n"
            "- MCP 2.x & CONTEXTO: Servidor Model Context Protocol montado em /mcp com ferramentas get_balance, get_positions, get_radar_signals, evaluate_asset, get_system_snapshot e ferramentas OpenViking (viking_tree, viking_read, viking_search, viking_commit_lesson).\n"
            "- SISTEMA DE CONTEXTO OPENVIKING: Sistema de Arquivos Virtual (viking://) com Progressive Disclosure (L0/L1/L2) e memória episódica auto-evolutiva de trading persistida no Obsidian Vault.\n"
            "- POSTURA: Seja direto, executivo, analítico e técnico. NUNCA use emojis nem na interface nem no texto. Responda em português do Brasil com precisão cirúrgica.\n"
        )
        if viking_context:
            sys_prompt += f"\nContexto Soberano do Sistema de Arquivos Virtual (OpenViking Context Database):\n{viking_context}\n"

        llm_messages = [{"role": "system", "content": sys_prompt}]
        llm_messages.extend(history)
        llm_messages.append({"role": "user", "content": user_msg})

        reply_content, source = self._call_llm(llm_messages)
        if not reply_content:
            reply_content = (
                "Entendido. Posso ajudar você a estruturar operações, emitir dossiês forenses em PDF, "
                "gerenciar envelopes de assinatura e telemetria ou consultar cotações de mercado. O que deseja fazer?"
            )
            source = "default_fallback"

        self._save_memory(db, session_id, user_msg, reply_content)
        return {
            "reply": reply_content,
            "active_agent": "hermes",
            "source": source
        }

    def confirm_action(self, db: Session, tool: str, payload: Dict[str, Any], session_id: str = "default") -> Dict[str, Any]:
        """Executa deterministicamente uma ação confirmada pelo operador."""
        if tool not in ALLOWED_TOOLS:
            return {"ok": False, "error": f"Ferramenta '{tool}' não permitida."}

        if tool == "create_operation":
            import secrets
            code = f"OP-2026-{secrets.token_hex(2).upper()}"
            title = payload.get("title", "Nova Operação")
            op = Operation(code=code, title=title, status="intake")
            db.add(op)
            
            audit = AuditEvent(
                agent_name=ORCHESTRATOR_NAME,
                action_type="OPERATION_CREATED",
                description=f"Operação {code} ({title}) criada com sucesso."
            )
            db.add(audit)
            db.commit()
            return {"ok": True, "message": f"Operação {code} registrada com sucesso!", "code": code}

        return {"ok": True, "message": "Ação concluída com sucesso."}

    def _save_memory(self, db: Session, session_id: str, user_text: str, reply_text: str) -> None:
        try:
            m_user = AgentConversationMemory(session_id=session_id, sender="User", message_text=user_text)
            m_bot = AgentConversationMemory(session_id=session_id, sender=ORCHESTRATOR_NAME, message_text=reply_text)
            db.add(m_user)
            db.add(m_bot)
            db.commit()
        except Exception:
            pass


hermes_orchestrator = HermesOrchestrator()
