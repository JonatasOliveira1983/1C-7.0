# -*- coding: utf-8 -*-
"""
1CRYPTEN 7.0 — OpenViking Context Database Engine (System 2 Episodic & Procedural Memory).
Implements the OpenViking virtual filesystem paradigm (viking://):
- viking://resources/ (MASTER_ARCHITECTURE.md, docs, engineering rules)
- viking://user/memories/ (preferences, patterns, cases, events)
- viking://agent/skills/ (.agents/skills execution SOPs)

Provides:
1. Three-Tier Progressive Disclosure (L0: Abstract, L1: Overview, L2: Detail)
2. Directory Recursive & Semantic Retrieval
3. Self-Evolving Memory on Trade Closure (Async Lesson Synthesis)
4. Model Context Protocol (MCP) and Hermes Orchestrator Integration
5. 100% Zero-Emoji Lamborghini / Binance Dark Technical Standards
"""

import os
import re
import time
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ContextLevel(IntEnum):
    """Níveis de contexto hierárquico do OpenViking."""
    ABSTRACT = 0  # L0: Resumo executivo (~100-300 caracteres)
    OVERVIEW = 1  # L1: Parâmetros operacionais e invariantes (~1K-2K caracteres)
    DETAIL = 2    # L2: Código-fonte, provas e logs detalhados (arquivo completo)


class VikingNode:
    """Nó do sistema de arquivos virtual viking://."""
    def __init__(
        self,
        uri: str,
        title: str,
        l0_abstract: str,
        l1_overview: str,
        l2_detail: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        updated_at: Optional[float] = None,
    ):
        self.uri = uri
        self.title = title
        self.l0_abstract = l0_abstract
        self.l1_overview = l1_overview
        self.l2_detail = l2_detail
        self.tags = tags or []
        self.metadata = metadata or {}
        self.updated_at = updated_at or time.time()

    def get_content(self, level: ContextLevel) -> str:
        if level == ContextLevel.ABSTRACT:
            return self.l0_abstract
        elif level == ContextLevel.OVERVIEW:
            return self.l1_overview
        return self.l2_detail


class OpenVikingContextService:
    """Serviço soberano de banco de dados de contexto OpenViking para o 1Crypten."""

    def __init__(self, root_dir: Optional[str] = None):
        if root_dir is None:
            self.root_dir = Path(__file__).resolve().parent.parent.parent
        else:
            self.root_dir = Path(root_dir)

        self.nodes: Dict[str, VikingNode] = {}
        self._initialized: bool = False

    def sync_all(self) -> Dict[str, Any]:
        """Sincroniza o sistema de arquivos virtual viking:// a partir dos arquivos do repositório."""
        t0 = time.time()
        self.nodes.clear()

        # ── 1. Diretórios Preset do Usuário (viking://user/memories/) ──
        self._register_user_preferences()
        self._register_canonical_patterns()
        self._register_historical_cases()

        # ── 2. Recursos Arquiteturais (viking://resources/) ──
        self._register_architecture_resources()
        self._register_docs_resources()

        # ── 3. Skills Executáveis (viking://agent/skills/) ──
        self._register_skills()

        self._initialized = True
        elapsed_ms = (time.time() - t0) * 1000.0

        return {
            "status": "online",
            "total_nodes": len(self.nodes),
            "elapsed_ms": round(elapsed_ms, 2),
            "roots": ["viking://resources", "viking://user", "viking://agent"],
        }

    # ── Registro de Memórias e Diretivas Canônicas ──

    def _register_user_preferences(self) -> None:
        """viking://user/memories/preferences/general"""
        uri = "viking://user/memories/preferences/general"
        l0 = "Diretrizes executivas do Almirante Jonatas: Padrão Binance Dark/Lamborghini, Zero Emojis e integridade total de dados."
        l1 = (
            "DIRETRIZES DE OPERAÇÃO DO ALMIRANTE JONATAS:\n"
            "1. Interface & Código: Estilo Binance Dark (#0B0E11 canvas, #1E2329 containers, #FCD535 gold, #0ECB81 verde, #F6465D vermelho).\n"
            "2. Zero Emojis: NUNCA utilizar emojis em respostas, logs, interfaces ou banco de dados. Apenas ícones vetoriais SVG e formatação limpa.\n"
            "3. Fonte Única da Verdade: Toda a verdade técnica reside em MASTER_ARCHITECTURE.md e backend.main:app (porta 8085).\n"
            "4. Verificação Empírica: Proibido declarar conclusões sem evidência de terminal e testes unitários executados."
        )
        l2 = l1 + "\n\nReferência canônica: AGENTS.md e .agents/rules/superpowers_methodology.md."
        self.nodes[uri] = VikingNode(
            uri=uri,
            title="Diretrizes do Usuário (Almirante Jonatas)",
            l0_abstract=l0,
            l1_overview=l1,
            l2_detail=l2,
            tags=["preferences", "user", "style", "invariants"],
        )

        # Banda Mandatória de Alavancagem (15X a 20X) [V172]
        uri_lev = "viking://user/memories/preferences/leverage_band"
        l0_lev = "Invariante de Alavancagem: Ordens da Laya Soberana exclusivamente em 15X ou 20X (sem valores intermediários). Proibido abrir abaixo de 15X."
        l1_lev = (
            "INVARIANTE DE ALAVANCAGEM OBRIGATÓRIA (15X A 20X):\n"
            "1. Faixa Soberana: Toda ordem autônoma aberta pela Laya deve operar exclusivamente com 15X ou 20X.\n"
            "2. Proibição Absoluta: Nenhuma ordem pode ser aberta com alavancagem inferior a 15X (veto irrestrito a 5x, 8x, 9x, 10x).\n"
            "3. Clamp Matemático: leverage = 20 if (calc_lev >= 18 or chosen.get('score', 0) >= 90) else 15 em backend/app/services/laya_router_service.py.\n"
            "4. Stop ROI Estrutural: target_stop_roi = 35.0 (~ -30% a -38% ROI) ancorado na distância estrutural de preço."
        )
        self.nodes[uri_lev] = VikingNode(
            uri=uri_lev,
            title="Invariante de Alavancagem Obrigatória (15X a 20X)",
            l0_abstract=l0_lev,
            l1_overview=l1_lev,
            l2_detail=l1_lev + "\n\nDeterminado pelo Almirante Jonatas em 26/10/2026 (V172).",
            tags=["preferences", "user", "leverage", "invariants", "laya"],
        )

    def _register_canonical_patterns(self) -> None:
        """viking://user/memories/patterns/*"""
        # Anti-Faca
        uri_faca = "viking://user/memories/patterns/anti_faca"
        l0_faca = "Escudo Anti-Faca: Veto irrevogável de SHORT em pump institucional (1C-EXP >= 70 ou diff >= 5.0%) e de LONG em dump (diff <= -6.0%)."
        l1_faca = (
            "PADRÃO OPERACIONAL ANTI-FACA (ANTI-KNIFE SHIELD):\n"
            "• Localização no Código: backend/app/services/laya_router_service.py (evaluate_dvwap_reversion e evaluate_range_boundary_reversal).\n"
            "• Regra SHORT: Veto se 1c_exp >= 70, ou bot_ignition == True, ou diff_pct >= 5.0% com candles verdes consecutivos.\n"
            "• Regra LONG: Veto se diff_pct <= -6.0% com candles vermelhos contínuos sem absorção de volume.\n"
            "• Objetivo: Impede tentar adivinhar topos contra robôs institucionais acelerando altcoins."
        )
        self.nodes[uri_faca] = VikingNode(
            uri=uri_faca,
            title="Escudo Anti-Faca (V167)",
            l0_abstract=l0_faca,
            l1_overview=l1_faca,
            l2_detail=l1_faca + "\n\nImplementado após o trade IRYS-USDT-SWAP.",
            tags=["patterns", "trading", "risk", "anti_knife", "laya"],
        )

        # Alt Pump Ignition (V169)
        uri_pump = "viking://user/memories/patterns/alt_pump_ignition"
        l0_pump = "Alt Pump Ignition: Setup prioritário. Identifica descolamento do BTC (Pearson < 0.45) + robôs ligados (1C-EXP >= 70) com Farol Macro BTC OBRIGATORIAMENTE favorável."
        l1_pump = (
            "PADRÃO ALT PUMP IGNITION (IGNIÇÃO INSTITUCIONAL V169):\n"
            "• Prioridade Soberana: Avaliado antes de qualquer tentativa de reversão à média.\n"
            "• Condições de Gatilho: 1c_exp >= 70 + Pearson < 0.45 + BTC.D em queda + BTC SEM SANGRIA (btc_trend_bias >= -0.4% e altcoin_long_allowed == True).\n"
            "• Veto Macro Inviolável: Se BTC estiver caindo (bloodbath ou trend bias < -0.4%), VETA compras de altcoins imediatamente.\n"
            "• Direção: LONG. Jamais operar SHORT contra ignição algorítmica de altcoin.\n"
            "• Alvo e Stop: Alvo no topo da banda de volatilidade, stop estrutural ATR saudável (2.0% a 3.8%)."
        )
        self.nodes[uri_pump] = VikingNode(
            uri=uri_pump,
            title="Alt Pump Ignition (V169)",
            l0_abstract=l0_pump,
            l1_overview=l1_pump,
            l2_detail=l1_pump,
            tags=["patterns", "trading", "ignition", "momentum", "laya", "v169"],
        )

        # Never Give Back (V169)
        uri_ngb = "viking://user/memories/patterns/never_give_back"
        l0_ngb = "Never Give Back V169: Breakeven acionado em +12% ROI travando +5% de lucro real (cobre taxas e slippage com ganho líquido)."
        l1_ngb = (
            "INVARIANTE NEVER GIVE BACK (DEFESA PROGRESSIVA V169):\n"
            "• Princípio: PnL positivo nunca pode virar prejuízo ou sair no zero a zero por ruído.\n"
            "• Degrau 0 (Inicial): Stop estrutural abaixo do suporte ATR com folga saudável (2.0% a 3.8%).\n"
            "• Degrau 1 (Breakeven): Ativado ao atingir +12.0% de ROI. Stop sobe para +5.0% de ROI (+3.05% líquido após taxas OKX).\n"
            "• Degrau 2 (Trailing 65%): Ao ultrapassar +14.0% de ROI, trailing protege 65% do pico de lucro.\n"
            "• Degraus Superiores: Permite o trade buscar alvos assimétricos de +25%, +35% e +50% ROI sem ser asfixiado."
        )
        self.nodes[uri_ngb] = VikingNode(
            uri=uri_ngb,
            title="Invariante Never Give Back (V169)",
            l0_abstract=l0_ngb,
            l1_overview=l1_ngb,
            l2_detail=l1_ngb,
            tags=["patterns", "trading", "trailing_stop", "risk", "never_give_back", "v169"],
        )

        # Stop Estrutural Anti-Mutilação (V169)
        uri_stop = "viking://user/memories/patterns/structural_stop_anti_mutilation"
        l0_stop = "Stop Estrutural Anti-Mutilação: Proibido amputar stops para 1.2% do preço. Stops têm respiro técnico de 2.0% a 3.8% com alavancagem adaptativa."
        l1_stop = (
            "DIRETRIZ DE STOP ESTRUTURAL ANTI-MUTILAÇÃO (V169):\n"
            "• Distância Técnica: Todo stop loss em altcoins deve respeitar a distância mínima de 2.0% a 3.8% de preço.\n"
            "• Alavancagem Adaptativa: Para calibrar a perda máxima em ~$28 sobre $100 de margem, a alavancagem se adapta à distância (calc_lev = int(28 / stop_dist_pct)), variando de 8x a 14x.\n"
            "• Fim do Clamp Artificial: Eliminada a antiga trava de -18% ROI que esmagava o preço do stop em míseros 1.2% gerando mortes no ruído."
        )
        self.nodes[uri_stop] = VikingNode(
            uri=uri_stop,
            title="Stop Estrutural Anti-Mutilação (V169)",
            l0_abstract=l0_stop,
            l1_overview=l1_stop,
            l2_detail=l1_stop,
            tags=["patterns", "trading", "stop_loss", "risk", "v169"],
        )

        # Quarentena 2h Pós-Stop Loss (V169)
        uri_quar = "viking://user/memories/patterns/symbol_quarantine_2h"
        l0_quar = "Quarentena Pós-SL: Ativo que tomou stop loss fica em quarentena inviolável de 2 horas (7200s), persistente em SQLite e memória."
        l1_quar = (
            "QUARENTENA INSTITUCIONAL PÓS-STOP LOSS (V169):\n"
            "• Duração: 7200 segundos (2 horas) a partir do timestamp do fechamento.\n"
            "• Persistência Dupla: Registrado em _symbol_cooldowns (RAM) e validado em sandbox_trades WHERE status='CLOSED_SL' (SQLite local_sniper.db).\n"
            "• Objetivo: Impede reentradas compulsivas (como ocorreu no caso ENA) no mesmo par recém-perdedor."
        )
        self.nodes[uri_quar] = VikingNode(
            uri=uri_quar,
            title="Quarentena 2h Pós-Stop Loss (V169)",
            l0_abstract=l0_quar,
            l1_overview=l1_quar,
            l2_detail=l1_quar,
            tags=["patterns", "trading", "cooldown", "anti_tilt", "v169"],
        )

        # Anti-Hedge
        uri_hedge = "viking://user/memories/patterns/anti_hedge"
        l0_hedge = "Anti-Hedge: Proibição estrita de abrir posições simultâneas opostas (LONG e SHORT) no mesmo par."
        l1_hedge = "Nunca abrir ordens LONG e SHORT concomitantes no mesmo símbolo. Uma nova ordem na direção oposta deve primeiro liquidar a ordem existente."
        self.nodes[uri_hedge] = VikingNode(
            uri=uri_hedge,
            title="Regra Anti-Hedge",
            l0_abstract=l0_hedge,
            l1_overview=l1_hedge,
            l2_detail=l1_hedge,
            tags=["patterns", "trading", "anti_hedge"],
        )
        # V175: WebSocket Dynamic Sync & Immediate Price Guard
        uri_v175_pat = "viking://user/memories/patterns/v175_dynamic_ws_price_guard"
        l0_v175_pat = "V175: Sincronizacao Dinamica WebSocket OKX e Guarda Imediata de Preco de Stop (RAM O(1) Sub-5ms) com Filtro de Pullback Intra-Range."
        l1_v175_pat = (
            "INVARIANTES DE MONITORAMENTO E STOP IMEDIATO (V175):\n"
            "• Sincronizacao Dinamica WebSocket: Toda ordem aberta adiciona seu par automaticamente ao okx_ws_public_service.sync_topics(), eliminando chamadas REST sincronas que geravam 429.\n"
            "• Guarda Imediata de Stop (Sub-5ms): Comparacao matematica instantanea no loop de 1s (Long <= stop_price, Short >= stop_price) que aciona stop_hit sem aguardar chamadas REST secundarias.\n"
            "• Filtro de Pullback Intra-Range: Em consolidacao/reversao a media, SHORT requer pullback estrutural (c_range >= 50% ou preco >= vwap; veto em c_range < 35%), e LONG requer dip (c_range <= 50% ou preco <= vwap; veto em c_range > 65%)."
        )
        self.nodes[uri_v175_pat] = VikingNode(
            uri=uri_v175_pat,
            title="V175: Sincronizacao Dinamica WebSocket & Guarda Imediata de Stop",
            l0_abstract=l0_v175_pat,
            l1_overview=l1_v175_pat,
            l2_detail=l1_v175_pat,
            tags=["patterns", "trading", "websocket", "stop_loss", "pullback", "guard", "v175"],
        )

        # Semântica PAPER vs REAL
        uri_balance = "viking://user/memories/patterns/unified_balance"
        l0_balance = "Semântica PAPER vs REAL: Em PAPER o Cockpit espelha a Banca Simulada Realizada; em REAL conecta diretamente à OKX."
        l1_balance = (
            "SEMÂNTICA UNIFICADA DE BANCA:\n"
            "• PAPER: Leitura via get_sandbox_unified_balance refletindo banca simulada com saldo base de $10.000,00.\n"
            "• REAL: Leitura de saldo real via OKX REST API v5 e envio direto de ordens ao book."
        )
        self.nodes[uri_balance] = VikingNode(
            uri=uri_balance,
            title="Semântica de Banca PAPER vs REAL",
            l0_abstract=l0_balance,
            l1_overview=l1_balance,
            l2_detail=l1_balance,
            tags=["patterns", "balance", "paper", "real"],
        )

    def _register_historical_cases(self) -> None:
        """viking://user/memories/cases/*"""
        # Caso IRYS
        uri_irys = "viking://user/memories/cases/case_irys_postmortem"
        l0_irys = "Caso IRYS-USDT-SWAP: Loss por tentativa de SHORT em altcoin com robôs ligados (+28% pump). Originou a V167 e o Escudo Anti-Faca."
        l1_irys = (
            "RELATÓRIO FORENSE DE TRADE (CASO IRYS):\n"
            "• Ativo: IRYS-USDT-SWAP | Data: 23/10/2026 | Estratégia: DVWAP_REVERSION | Direção: SHORT | Loss: -18% ROI.\n"
            "• Causa-Raiz: O motor DVWAP interpretou afastamento de +28.2% como sobrecompra, mas o ativo estava em ignição algorítmica (1C-EXP >= 70) com candles verdes de 5m/15m sem reversão.\n"
            "• Resolução Permanente: Implementação do Escudo Anti-Faca e unificação da prioridade Alt Pump Ignition na V167."
        )
        self.nodes[uri_irys] = VikingNode(
            uri=uri_irys,
            title="Pós-Morte do Trade IRYS (V167)",
            l0_abstract=l0_irys,
            l1_overview=l1_irys,
            l2_detail=l1_irys + "\n\nRegistrado no Obsidian Vault em vault_galaxy/journal/2026-10-23.md.",
            tags=["cases", "postmortem", "loss_analysis", "irys"],
        )

    def _register_architecture_resources(self) -> None:
        """viking://resources/architecture/*"""
        arch_path = self.root_dir / "MASTER_ARCHITECTURE.md"
        if arch_path.exists():
            try:
                content = arch_path.read_text(encoding="utf-8")
                l0 = "MASTER_ARCHITECTURE.md: Fonte Única da Verdade do 1Crypten 7.0 (V167). Entry point backend.main:app porta 8085."
                l1 = (
                    "ARQUITETURA CANÔNICA DO 1CRYPTEN 7.0:\n"
                    "• Entry Point Único: backend.main:app (porta 8085).\n"
                    "• Camada System 1: Laya Sovereign Brain (laya_router_service.py) rodando em CPU em microssegundos.\n"
                    "• Camada System 2: Hermes Orchestrator (hermes_service.py) coordenando compliance, OSINT e memória.\n"
                    "• Farol Macro BTC: Monitoramento contínuo de ADX, dominância BTC.D e correlação de Pearson em BTC-USDT-SWAP."
                )
                self.nodes["viking://resources/architecture/master"] = VikingNode(
                    uri="viking://resources/architecture/master",
                    title="MASTER_ARCHITECTURE.md (SSOT)",
                    l0_abstract=l0,
                    l1_overview=l1,
                    l2_detail=content,
                    tags=["resources", "architecture", "master"],
                )

                # V174: Liquidity Zones & Encryptos Methodology
                uri_v174 = "viking://resources/architecture/v174_liquidity_zones"
                l0_v174 = "V174: Motor de 3 Zonas de Liquidez Encryptos (Hunt >= 1.5%, Dead Zone 0.3%-1.5%, Exhaustion < 0.3%) e Heatmap O(1) na Laya 360."
                l1_v174 = (
                    "METODOLOGIA ENCRYPTOS (CICLO EM 3 ZONAS):\n"
                    "1. ZONA 1 (HUNT - Atração Ativa): Distância >= 1.5% -> Entrada a favor do ímã permitida (Take Profit na borda do bolsão).\n"
                    "2. ZONA 2 (DEAD_ZONE - Veto de Entrada): Distância 0.3% a 1.5% -> Veto estrito de novas entradas para neutralizar falso rompimento.\n"
                    "3. ZONA 3 (EXHAUSTION - Varredura & Reversão): Distância < 0.3% -> Gatilho de reversão imediata condicionado a pavio >= 30% (TICK_REJECTION_INDEX)."
                )
                self.nodes[uri_v174] = VikingNode(
                    uri=uri_v174,
                    title="V174: Ciclo de 3 Zonas de Liquidez & Metodologia Encryptos",
                    l0_abstract=l0_v174,
                    l1_overview=l1_v174,
                    l2_detail=l1_v174 + "\n\nImplementado em backend/app/services/coinglass_heatmap_service.py e renderizado no Canvas Retina da Laya 360.",
                    tags=["resources", "architecture", "v174", "encryptos", "liquidity", "heatmap"]
                )
                # V175: WebSocket Dynamic Sync & Immediate Price Guard
                uri_v175 = "viking://resources/architecture/v175_ws_sync_immediate_price_guard"
                l0_v175 = "V175: Sincronizacao Dinamica WebSocket OKX e Guarda Imediata de Preco de Stop (RAM O(1) Sub-5ms) com Filtro de Pullback Intra-Range."
                l1_v175 = (
                    "INVARIANTES DE MONITORAMENTO E STOP IMEDIATO (V175):\n"
                    "1. Sincronizacao Dinamica WebSocket: Toda ordem aberta adiciona seu par automaticamente ao okx_ws_public_service.sync_topics(), eliminando chamadas REST sincronas que geravam 429.\n"
                    "2. Guarda Imediata de Stop (Sub-5ms): Comparacao matematica instantanea no loop de 1s (Long <= stop_price, Short >= stop_price) que aciona stop_hit sem aguardar chamadas REST secundarias.\n"
                    "3. Filtro de Pullback Intra-Range: Em consolidacao/reversao a media, SHORT requer pullback estrutural (c_range >= 50% ou preco >= vwap; veto em c_range < 35%), e LONG requer dip (c_range <= 50% ou preco <= vwap; veto em c_range > 65%)."
                )
                self.nodes[uri_v175] = VikingNode(
                    uri=uri_v175,
                    title="V175: Sincronizacao Dinamica WebSocket & Guarda Imediata de Stop",
                    l0_abstract=l0_v175,
                    l1_overview=l1_v175,
                    l2_detail=l1_v175 + "\n\nImplementado em backend/services/sandbox_service.py e backend/app/services/laya_router_service.py.",
                    tags=["resources", "architecture", "v175", "websocket", "stop_loss", "pullback", "guard"]
                )
            except Exception:
                pass

    def _register_docs_resources(self) -> None:
        """viking://resources/docs/*"""
        docs_dir = self.root_dir / "docs"
        if docs_dir.exists():
            for p in docs_dir.glob("*.md"):
                rel = p.stem.lower().replace(" ", "_")
                uri = f"viking://resources/docs/{rel}"
                try:
                    text = p.read_text(encoding="utf-8")
                    first_line = text.splitlines()[0] if text.splitlines() else p.name
                    l0 = f"Documento técnico {p.name}: {first_line[:120]}"
                    l1 = "\n".join(text.splitlines()[:30])
                    self.nodes[uri] = VikingNode(
                        uri=uri,
                        title=f"Doc: {p.name}",
                        l0_abstract=l0,
                        l1_overview=l1,
                        l2_detail=text,
                        tags=["resources", "docs", rel],
                    )
                except Exception:
                    pass

    def _register_skills(self) -> None:
        """viking://agent/skills/*"""
        skills_dir = self.root_dir / ".agents" / "skills"
        if skills_dir.exists():
            for skill_path in skills_dir.glob("*/SKILL.md"):
                skill_name = skill_path.parent.name
                uri = f"viking://agent/skills/{skill_name}"
                try:
                    text = skill_path.read_text(encoding="utf-8")
                    l0 = f"Skill executável {skill_name}: Procedimento padronizado do repositório."
                    l1 = "\n".join([line for line in text.splitlines() if line.startswith("#") or line.startswith("-")][:20])
                    self.nodes[uri] = VikingNode(
                        uri=uri,
                        title=f"Skill: {skill_name}",
                        l0_abstract=l0,
                        l1_overview=l1,
                        l2_detail=text,
                        tags=["agent", "skills", skill_name],
                    )
                except Exception:
                    pass

    # ── Operações de Navegação Virtual (viking://) ──

    def ls(self, uri: str = "viking://") -> List[str]:
        """Lista os filhos diretos de um caminho virtual."""
        if not self._initialized:
            self.sync_all()

        norm = uri.rstrip("/")
        if norm in ("viking:", "viking:/", "viking://"):
            return ["resources", "user", "agent"]

        # Extrai subpastas
        prefix = norm + "/"
        children = set()
        for k in self.nodes.keys():
            if k.startswith(prefix):
                rest = k[len(prefix):]
                part = rest.split("/")[0]
                children.add(part)

        return sorted(list(children))

    def tree(self, uri: str = "viking://") -> Dict[str, Any]:
        """Gera uma árvore hierárquica a partir do URI especificado."""
        if not self._initialized:
            self.sync_all()

        norm = uri.rstrip("/")
        out: Dict[str, Any] = {}

        for k in sorted(self.nodes.keys()):
            if norm == "viking://" or norm == "viking:" or k.startswith(norm):
                clean_path = k.replace("viking://", "")
                parts = clean_path.split("/")
                curr = out
                for idx, p in enumerate(parts):
                    if idx == len(parts) - 1:
                        curr[p] = k
                    else:
                        if p not in curr or not isinstance(curr[p], dict):
                            curr[p] = {}
                        curr = curr[p]

        # Se consultou um nó específico, filtra
        if norm not in ("viking:", "viking:/", "viking://"):
            sub_parts = norm.replace("viking://", "").split("/")
            curr = out
            for sp in sub_parts:
                if sp in curr and isinstance(curr[sp], dict):
                    curr = curr[sp]
                else:
                    return curr
            return curr

        return out

    def read(self, uri: str, level: ContextLevel = ContextLevel.OVERVIEW) -> Optional[str]:
        """Lê o conteúdo de um nó no nível de granularidade solicitado (L0, L1 ou L2)."""
        if not self._initialized:
            self.sync_all()

        node = self.nodes.get(uri)
        if not node:
            # Tenta busca flexível por sufixo
            for k, v in self.nodes.items():
                if k.endswith(uri) or uri in k:
                    node = v
                    break

        if not node:
            return None

        return node.get_content(level)

    def search(
        self,
        query: str,
        level: ContextLevel = ContextLevel.OVERVIEW,
        namespace_filter: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Busca estruturada por palavras-chave com pontuação nos níveis de contexto."""
        if not self._initialized:
            self.sync_all()

        q_terms = [t for t in re.sub(r"[^\w\s-]", " ", query.lower()).split() if len(t) > 2]
        if not q_terms:
            return []

        scored = []
        for uri, node in self.nodes.items():
            if namespace_filter and not uri.startswith(namespace_filter):
                continue

            content = node.get_content(level).lower()
            title = node.title.lower()
            tags = " ".join(node.tags).lower()

            score = 0.0
            for term in q_terms:
                if term in title:
                    score += 5.0
                if term in tags:
                    score += 3.0
                if term in content:
                    score += 1.0

            if score > 0:
                scored.append({
                    "uri": uri,
                    "title": node.title,
                    "level": int(level),
                    "score": round(score, 2),
                    "content": node.get_content(level),
                    "tags": node.tags,
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    # ── Memória Auto-Evolutiva (Trade Closure Synthesis) ──

    def record_trade_closure(self, trade: Dict[str, Any]) -> VikingNode:
        """
        Gera e persiste um aprendizado episódico a partir do encerramento de um trade.
        Atualiza o grafo em viking://user/memories/cases/ e persiste no Obsidian Vault.
        """
        if not self._initialized:
            self.sync_all()

        symbol = trade.get("symbol", "UNKNOWN")
        strategy = trade.get("strategy", "UNKNOWN")
        direction = trade.get("direction", "UNKNOWN")
        pnl_pct = float(trade.get("pnl_pct") or 0.0)
        exit_reason = trade.get("exit_reason", "MANUAL_CLOSE")
        meta = trade.get("contract_meta") or {}
        if isinstance(meta, str):
            import json
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}

        trade_id = trade.get("id") or f"trade_{int(time.time())}"
        clean_sym = symbol.replace("-USDT-SWAP", "").replace("USDT", "")
        slug = f"case_{clean_sym.lower()}_{trade_id}"
        uri = f"viking://user/memories/cases/{slug}"

        is_win = pnl_pct > 0
        outcome = "LUCRO" if is_win else "PREJUÍZO"
        sign = "+" if pnl_pct >= 0 else ""

        l0 = (
            f"Caso {symbol} ({direction} 15X): {outcome} de {sign}{pnl_pct:.2f}% "
            f"via {strategy}. Motivo de saída: {exit_reason}."
        )

        rationale = meta.get("rationale", "Sem justificativa técnica registrada.")
        l1 = (
            f"APRENDIZADO EPISÓDICO DE TRADE — {symbol}\n"
            f"• Direção & Alavancagem: {direction} (15X Isolada)\n"
            f"• Estratégia Acionada: {strategy}\n"
            f"• Resultado Final: {outcome} ({sign}{pnl_pct:.2f}%)\n"
            f"• Gatilho de Fechamento: {exit_reason}\n"
            f"• Contexto Tático de Entrada: {rationale}\n"
            f"• Regra Canônica Aplicável: {'Invariante Never Give Back' if is_win else 'Escudo Anti-Faca e Stop ATR'}.\n"
            f"• Diretriz Futura: {'Replicar confluência com trailing stops travados' if is_win else 'Verificar exaustão de volume antes de autorizar entrada'}.\n"
        )

        l2 = l1 + f"\nPayload Bruto do Contrato:\n{str(meta)}"

        node = VikingNode(
            uri=uri,
            title=f"Caso {clean_sym} ({outcome} {sign}{pnl_pct:.2f}%)",
            l0_abstract=l0,
            l1_overview=l1,
            l2_detail=l2,
            tags=["cases", "trade_closure", clean_sym.lower(), strategy.lower(), "auto_evolution"],
        )

        self.nodes[uri] = node

        # Persistência em disco no Obsidian Vault
        self._append_to_vault_journal(node)

        return node

    def commit_lesson(self, category: str, title: str, content: str, tags: Optional[List[str]] = None) -> VikingNode:
        """Permite commit manual ou autônomo de novas memórias ou diretivas."""
        if not self._initialized:
            self.sync_all()

        clean_slug = re.sub(r"[^\w-]", "_", title.lower())
        cat_clean = category.strip().lower()
        uri = f"viking://user/memories/{cat_clean}/{clean_slug}"

        l0 = f"{title}: {content[:150]}"
        l1 = f"{title.upper()}\n{content}"
        l2 = l1

        node = VikingNode(
            uri=uri,
            title=title,
            l0_abstract=l0,
            l1_overview=l1,
            l2_detail=l2,
            tags=["user", "memories", cat_clean] + (tags or []),
        )

        self.nodes[uri] = node
        return node

    def _append_to_vault_journal(self, node: VikingNode) -> None:
        """Garante persistência física no Obsidian Vault em vault_galaxy/journal/."""
        try:
            today_str = time.strftime("%Y-%m-%d")
            journal_path = self.root_dir / "vault_galaxy" / "journal" / f"{today_str}.md"
            journal_path.parent.mkdir(parents=True, exist_ok=True)

            entry = (
                f"\n\n### [OPENVIKING-EPISODE] {node.title}\n"
                f"- **URI**: `{node.uri}`\n"
                f"- **Data/Hora**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"- **Síntese L0**: {node.l0_abstract}\n\n"
                f"```text\n{node.l1_overview}\n```\n"
            )

            if journal_path.exists():
                with open(journal_path, "a", encoding="utf-8") as f:
                    f.write(entry)
            else:
                with open(journal_path, "w", encoding="utf-8") as f:
                    f.write(f"# DIÁRIO DE TRADING E MEMÓRIA AGÊNTICA — {today_str}\n" + entry)
        except Exception:
            pass

    # ── Síntese de Prompt Hierárquico para o Hermes ──

    def get_hierarchical_context_for_prompt(self, query: str, max_tokens: int = 1500) -> str:
        """
        Constrói contexto de alta densidade sem inchaço de tokens:
        - L0 das Preferências do Usuário
        - L1 dos Padrões de Risco Cruciais (Anti-Faca, Never Give Back)
        - L1 das Lições e Casos Recentes
        - L1 de Recursos específicos encontrados pela query
        """
        if not self._initialized:
            self.sync_all()

        blocks: List[str] = [
            "[OPENVIKING // VIKING CONTEXT DATABASE]",
            "STATUS DO GRAFO: viking:// ATIVO | PARADIGMA: SISTEMA DE ARQUIVOS VIRTUAL",
            "",
            "=== VIKING PREFERENCES (viking://user/memories/preferences) ===",
            self.read("viking://user/memories/preferences/general", level=ContextLevel.OVERVIEW) or "",
            "",
            "=== VIKING TRADING PATTERNS (viking://user/memories/patterns) ===",
            "• " + (self.read("viking://user/memories/patterns/anti_faca", level=ContextLevel.ABSTRACT) or ""),
            "• " + (self.read("viking://user/memories/patterns/alt_pump_ignition", level=ContextLevel.ABSTRACT) or ""),
            "• " + (self.read("viking://user/memories/patterns/never_give_back", level=ContextLevel.ABSTRACT) or ""),
            "• " + (self.read("viking://user/memories/patterns/anti_hedge", level=ContextLevel.ABSTRACT) or ""),
            "",
            "=== VIKING RECENT CASES & LESSONS (viking://user/memories/cases) ===",
        ]

        # Adiciona casos recentes (L0)
        case_nodes = [n for uri, n in self.nodes.items() if uri.startswith("viking://user/memories/cases")]
        case_nodes.sort(key=lambda x: x.updated_at, reverse=True)
        for c in case_nodes[:3]:
            blocks.append(f"• {c.l0_abstract}")

        # Busca específica pela query
        matches = self.search(query, level=ContextLevel.OVERVIEW, limit=2)
        if matches:
            blocks.append("\n=== RECURSOS RELEVANTES DO GRAFO (viking://search) ===")
            for m in matches:
                # Evita duplicar o que já foi injetado nas seções padrão
                if "preferences" not in m["uri"] and "anti_faca" not in m["uri"] and "never_give_back" not in m["uri"]:
                    blocks.append(f"[{m['uri']}]\n{m['content']}")

        full_text = "\n".join(blocks).strip()
        # Trunca de forma segura para não estourar max_tokens (~4 chars por token)
        max_chars = max_tokens * 4
        if len(full_text) > max_chars:
            full_text = full_text[:max_chars] + "\n... [Contexto OpenViking truncado no limite de tokens]"

        return full_text


# Instância Singleton global
openviking_context_service = OpenVikingContextService()
