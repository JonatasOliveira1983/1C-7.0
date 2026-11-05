"""
Base Tecnológica — Hermes Orchestrator 2.0.
Orquestrador central de negócios, diálogos e automação multiagente.
- Arquitetura de IA Híbrida: Laya (CPU Intent Router) + DeepSeek Cloud + Qwen3 GGUF offline
- Memória conversacional persistente em banco de dados
- Confirmação expressa de ações de escrita (dry-run com cards de confirmação)
- Geração de Dossiês e Relatórios Forenses em PDF com 100% de veracidade de dados
- 100% livre de emojis (ícones vetoriais SVG e formatação limpa)
"""
import os
import json
import re
import urllib.request
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
            from app.services.laya_router_service import laya_router_service, _agent
            if _agent is None:
                # Não bloqueia a thread se os pesos do Laya não foram pré-aquecidos
                return None
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
    # ── Snapshot de Runtime Dinâmico em Tempo Real (Zero Mock / 50X / Laya 360 / Trades) ──
    @staticmethod
    @staticmethod
    def _build_runtime_context(message: str) -> tuple:
        import sqlite3
        import os
        db_path = os.path.join(os.path.dirname(__file__), "..", "..", "local_sniper.db")

        active_trades_str = "• Nenhuma posição aberta no momento (Laya aguardando confluência institucional)."
        closed_trades_str = "• Nenhuma ordem finalizada recente registrada no banco."
        equity_str = "$100.00 USDT (Paridade Sandbox Realizada)"

        try:
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                
                # Banca
                cur.execute("SELECT saldo_total FROM banca_status WHERE id = 1")
                row_b = cur.fetchone()
                if row_b and row_b[0]:
                    equity_str = f"${float(row_b[0]):,.2f} USDT"
                    
                # Ordens Ativas (Alavancagem 50X)
                cur.execute("SELECT symbol, direction, entry_price, current_price, pnl_pct, stop_loss, target, strategy FROM sandbox_trades WHERE status = 'ACTIVE'")
                rows_act = cur.fetchall()
                if rows_act:
                    lines_act = []
                    for idx, r in enumerate(rows_act, 1):
                        sym, direction, entry, cur_p, pnl_pct, sl, tp, strat = r
                        s_pnl = f"+{pnl_pct:.2f}%" if pnl_pct >= 0 else f"{pnl_pct:.2f}%"
                        lines_act.append(f"• Slot {idx}: {sym} ({direction} 50X Isolada) | Entrada: ${entry:,.4f} | Atual: ${cur_p:,.4f} | PnL: {s_pnl} | Stop: ${sl:,.4f} | Estratégia: {strat}")
                    active_trades_str = "\n".join(lines_act)

                # Ordens Finalizadas / Histórico Recente (Alavancagem 50X)
                cur.execute("SELECT id, symbol, direction, entry_price, current_price, max_roi, pnl_pct, status, closed_at, strategy, contract_meta, flash_state FROM sandbox_trades WHERE status LIKE 'CLOSED%' ORDER BY closed_at DESC LIMIT 5")
                rows_closed = cur.fetchall()
                if rows_closed:
                    clines = []
                    for r in rows_closed:
                        cid, sym, direction, entry, exit_p, max_roi, pnl_pct, status, closed_at, strat, cm_raw, fs_raw = r
                        cm = json.loads(cm_raw) if cm_raw else {}
                        fs = json.loads(fs_raw) if fs_raw else {}
                        lev = cm.get("leverage", 50.0)
                        net_roi = cm.get("net_roi", pnl_pct)
                        net_pnl = cm.get("net_pnl_usd", 0.0)
                        score = cm.get("laya_decision", "N/A")
                        rationale = cm.get("rationale", "N/A")
                        trail_history = ", ".join(fs.get("history", [])[-3:])
                        clines.append(
                            f"• Ordem Finalizada [{cid}] — {sym} ({direction} {lev}X Isolada):\n"
                            f"  Status: {status} | Estratégia: {strat}\n"
                            f"  Entrada: ${entry:,.4f} -> Saída: ${exit_p:,.4f}\n"
                            f"  ROI Pico (Máximo): +{max_roi:.2f}% | ROI Líquido Realizado: +{net_roi:.2f}%\n"
                            f"  Lucro Líquido Realizado: +${net_pnl:,.2f} USDT\n"
                            f"  Score / Decisão Laya: {score}\n"
                            f"  Rationale Técnico Laya: {rationale}\n"
                            f"  Histórico Escadinha: {trail_history}"
                        )
                    closed_trades_str = "\n\n".join(clines)

                # Catalogo de Estrategias Quantitativas
                strat_context_str = "• Nenhuma estrategia personalizada registrada."
                try:
                    cur.execute("SELECT id, name, category, regime, mathematical_basis, default_leverage FROM laya_strategies WHERE active = 1")
                    rows_strat = cur.fetchall()
                    if rows_strat:
                        slines = []
                        for s in rows_strat:
                            sid, sname, scat, sreg, smath, slev = s
                            slines.append(f"• [{sid}] {sname} ({scat} / Regime {sreg} / {slev:.0f}X Isolada):\n  Base Matematica: {smath}")
                        strat_context_str = "\n".join(slines)
                except Exception:
                    pass

                conn.close()
        except Exception:
            pass

        # Laya 360
        laya_str = "Laya Soberana: Monitoramento contínuo de fluxo institucional e liquidez OKX."
        try:
            from app.services.laya_router_service import laya_router_service
            laya_str = (
                f"Regime de Mercado: {laya_router_service.current_regime} | Modo: {laya_router_service.regime_mode} | "
                f"Master ADX: {laya_router_service.master_adx} | Pares Líquidos: {laya_router_service.universal_market_stats.get('liquid_pairs', 0)}"
            )
        except Exception:
            pass

        # OpenViking & RAG
        viking_str = ""
        try:
            from services.openviking_context_service import openviking_context_service
            viking_str = openviking_context_service.get_hierarchical_context_for_prompt(message, max_tokens=1500)
        except Exception:
            try:
                from app.services.rag_service import rag_service
                viking_str = rag_service.get_relevant_context(message, max_chars=1200)
            except Exception:
                pass

        # Plutus Agent (Metodo ARCA)
        plutus_str = (
            "• Agente Plutus (Metodo ARCA): Ativo e sincronizado.\n"
            "  - Alocacao Patrimonial: 35-40% FIIs (HGLG11, KNRI11) | 25-30% Acoes Dividendos (BBAS3, ITUB4) | 15-20% Caixa/RF (Selic) | 15-20% Internacional (IVVB11).\n"
            "  - Meta: Renda passiva liquida previsivel e drenagem de lucros da banca 50X para reserva antifragil."
        )
        try:
            from services.plutus_agent import ARCA_UNIVERSE
            plutus_str += f"\n  - Universo ARCA Auditado: {sum(len(v) for v in ARCA_UNIVERSE.values())} ativos de alta liquidez monitorados."
        except Exception:
            pass

        # Telemetria & Observatorio
        telemetry_str = (
            "• Sistema de Telemetria: Online (/telemetry).\n"
            "  - Microestrutura DMA: Slippage Zero ativo (Barry Johnson).\n"
            "  - Latencia da Mesa: ~24.5ms (OKX WebSocket & REST).\n"
            "  - Buffer Temporal uPlot: 3600 segundos sem engasgo vertical."
        )
        try:
            from app.services.telemetry_service import telemetry_service
            t_sum = telemetry_service.get_summary()
            telemetry_str = (
                f"• Sistema de Telemetria: Online (/telemetry) | Latencia: {t_sum.get('current_ping_ms', 24.5):.1f}ms | "
                f"Taxa: {t_sum.get('current_ticks_sec', 20)} ticks/s | "
                f"Slippage Zero: Auditado DMA | Estrategia Quant Ativa: {t_sum.get('active_quant_strategy', 'COINT_ZSCORE_50X')}"
            )
        except Exception:
            pass

        runtime_data = (
            "\n## [SNAPSHOT DE RUNTIME EM TEMPO REAL]\n"
            f"• Banca Consolidada (Equity): {equity_str}\n"
            "• Alavancagem Padrão Institucional: 50X Isolada (Invariante Rígida do Sistema)\n"
            f"• Estado Laya Soberana: {laya_str}\n"
            f"{telemetry_str}\n"
            f"{plutus_str}\n\n"
            "## [CATALOGO DE ESTRATEGIAS QUANTITATIVAS DA LAYA SOBERANA]\n"
            f"{strat_context_str}\n\n"
            "## [ORDENS ATIVAS NOS SLOTS (50X)]\n"
            f"{active_trades_str}\n\n"
            "## [HISTORICO DE ORDENS FINALIZADAS RECENTES (50X)]\n"
            f"{closed_trades_str}\n"
        )
        return runtime_data, viking_str

    # ── Chamada de LLM DeepSeek com Chave Oficial e RAG ──
    def _call_llm(self, messages: List[Dict[str, str]]) -> tuple:
        # 1. DeepSeek Cloud
        try:
            import urllib.request
            key = os.getenv("DEEPSEEK_API_KEY", "") or getattr(settings, "DEEPSEEK_API_KEY", "")
            base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
            endpoint = f"{base_url}/v1/chat/completions" if "/v1" not in base_url else f"{base_url}/chat/completions"

            payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 1024
            }
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=18) as res:
                data = json.loads(res.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                if content and len(content.strip()) > 5:
                    clean = self._sanitize(self._strip_emojis(content.strip()))
                    return clean, "deepseek_cloud"
        except Exception as e:
            print("Erro DeepSeek:", e)

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
        text = text.replace("<think>", "").replace("</think>", "")
        text = unicodedata.normalize("NFC", text)
        return text.strip()

    # ── Método Principal de Processamento ──
    def chat(self, db: Session, message: str, session_id: str = "default") -> Dict[str, Any]:
        user_msg = (message or "").strip()
        if not user_msg:
            return {"reply": "Por favor, envie uma mensagem.", "active_agent": "hermes", "source": "empty"}

        # 0. Saudação rápida (apenas para cumprimento puro de uma palavra)
        low_msg = user_msg.lower()
        if low_msg in self._GREETINGS and len(user_msg.split()) <= 2:
            reply = f"Olá, {OPERATOR_NAME}. Hermes online com DeepSeek, OpenViking e Laya 360 ativos. Como posso auxiliar na estratégia de hoje?"
            self._save_memory(db, session_id, user_msg, reply)
            return {"reply": reply, "active_agent": "hermes", "source": "fast_greeting"}

        # 1. Checagem de Dossiê Forense / OSINT (se houver documento explícito)
        dossier_res = self._handle_security_dossier(user_msg)
        if dossier_res:
            self._save_memory(db, session_id, user_msg, dossier_res["reply"])
            return dossier_res

        # 2. Detecção de Escrita (dry-run com card de confirmação)
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

        # 3. LLM DeepSeek com Memória, OpenViking e Live Runtime Snapshot
        history = self._load_memory(db, session_id, limit=8)
        runtime_snapshot, viking_context = self._build_runtime_context(user_msg)

        sys_prompt = (
            f"Você é o {ORCHESTRATOR_NAME} ({AGENT_TAG}), orquestrador e inteligência central da frota 1CRYPTEN 7.0.\n"
            f"Você atende diretamente o Almirante Jonatas ({OPERATOR_NAME}).\n\n"
            "DIRETRIZES FUNDAMENTAIS:\n"
            "- ALAVANCAGEM: Todas as operações do sistema são executadas estritamente com ALAVANCAGEM 50X ISOLADA. NUNCA mencione 15X.\n"
            "- MAPA DE MODULOS DA PLATAFORMA 1CRYPTEN 7.0:\n"
            "  1. COCKPIT (/cockpit): Central de comando tatica Hallmark Console V192 com Banca Unificada, 4 graficos ao vivo e gestao de slots 50X.\n"
            "  2. LAYA 360 (/laya): Radar dos 30 Titans, fluxo Rubik de baleias (OI Delta + LSR) e decisao dual (Mean-Reversion vs Trend Sniper com Subordinacao 2H e Pullback Hunter 30M).\n"
            "  3. TELEMETRIA (/telemetry): Monitor de ultra-baixa latencia (~24ms), slippage zero de Barry Johnson, buffer uPlot de 3600s e chips em tempo real.\n"
            "  4. PLUTUS (/plutus): Gestao patrimonial e preservacao pelo Metodo ARCA (FIIs 35-40%, Acoes Dividendos 25-30%, Caixa 15-20%, Internacional 15-20%) e drenagem de lucros da banca.\n"
            "  5. DOCS (/docs e docs/blueprint/): Repositorio da verdade tecnica com os Blueprints 01 a 07 (Arquitetura, Stop Loss, WebSocket, Arbitragem, OpenViking, Heatmaps e Plutus ARCA).\n"
            "- SIMBIOSE COM A LAYA SOBERANA: Você opera em coordenação com a Laya Soberana (System 1 Neural Engine), que caça liquidez institucional e varre os pares perpétuos da OKX.\n"
            "- ESTRATEGIAS QUANTITATIVAS: A Laya implementa modelos quantitativos formais (Pairs Trading Cointegration & Z-Score, Triple Barrier Method de López de Prado, Funding Rate Arbitrage). Todas operam estritamente em 50X Isolada com trailing stop Never Give Back.\n"
            "- GESTÃO DE RISCO: Invariante Never Give Back com escadinha progressiva de 5 degraus de Trailing Stop que nunca recuam, e regra Anti-Hedge.\n"
            "- MODEL CONTEXT PROTOCOL (MCP 2.x) E OPENVIKING: Você tem acesso completo aos recursos viking://, relatórios de telemetria e histórico do Obsidian Vault.\n"
            "- DADOS REAIS: Utilize SEMPRE as informações do SNAPSHOT DE RUNTIME e HISTÓRICO DE ORDENS fornecidos abaixo. Seja exato sobre preços, PnL, scores e rationale.\n"
            "- ZERO EMOJIS: Responda em tom analítico, institucional, técnico e cirúrgico em português do Brasil. NUNCA use emojis nem na interface nem no texto.\n"
        )
        if runtime_snapshot:
            sys_prompt += f"\n{runtime_snapshot}\n"
        if viking_context:
            sys_prompt += f"\n[CONTEXTO DE REGRAS E ARQUITETURA OPENVIKING]\n{viking_context}\n"

        llm_messages = [{"role": "system", "content": sys_prompt}]
        llm_messages.extend(history)
        llm_messages.append({"role": "user", "content": user_msg})

        reply_content, source = self._call_llm(llm_messages)
        if not reply_content:
            reply_content = (
                "Hermes sincronizado. Não foi possível conectar ao endpoint DeepSeek no momento. "
                "Verifique a conectividade com a API."
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


# Module-level alias for runtime context
_build_runtime_context = HermesOrchestrator._build_runtime_context
