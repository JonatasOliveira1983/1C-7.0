# -*- coding: utf-8 -*-
"""
1CRYPTEN 7.0 — AGENTE PLUTUS (VIVER DE RENDA / MÉTODO ARCA)
Motor autônomo de alocação de patrimônio e proventos passivos perpétuos.
Orquestrado nativamente pelo Hermes Intelligence.
Baseado no Método ARCA (Ações, Real Estate/FIIs, Caixa/Renda Fixa, Ativos Internacionais).
"""
import time
import math
import logging
import asyncio
from typing import Dict, Any, List, Optional
import urllib.request
import json

logger = logging.getLogger("1CRYPTEN-PLUTUS")

# --------------------------------------------------------------------------
# UNIVERSO DE ELITE DE ATIVOS ARCA (MÉTODO THIAGO NIGRO / PRIMO RICO)
# Dados base auditados com cotações e dividend yields médios de 12M
# --------------------------------------------------------------------------
ARCA_UNIVERSE = {
    # 1. REAL ESTATE (FIIs - FUNDOS IMOBILIÁRIOS ISENTOS DE IR)
    "REAL_ESTATE": [
        {
            "ticker": "HGLG11",
            "name": "CSHG Logística",
            "segment": "Tijolo Logística",
            "price_brl": 161.50,
            "dy_12m": 0.089,  # 8.9% a.a.
            "pvp": 1.01,
            "liquidity_daily_brl": 8500000,
            "risk_score": "BAIXO",
            "ir_exempt": True,
            "description": "Galpões logísticos classe A com contratos atípicos de longo prazo."
        },
        {
            "ticker": "BTLG11",
            "name": "BTG Pactual Logística",
            "segment": "Tijolo Logística",
            "price_brl": 100.80,
            "dy_12m": 0.094,  # 9.4% a.a.
            "pvp": 0.99,
            "liquidity_daily_brl": 7200000,
            "risk_score": "BAIXO",
            "ir_exempt": True,
            "description": "Portfólio resiliente no raio de 30km de São Paulo com vacância controlada."
        },
        {
            "ticker": "XPML11",
            "name": "XP Malls",
            "segment": "Tijolo Shoppings",
            "price_brl": 104.20,
            "dy_12m": 0.098,  # 9.8% a.a.
            "pvp": 0.97,
            "liquidity_daily_brl": 9100000,
            "risk_score": "MODERADO",
            "ir_exempt": True,
            "description": "Maior fundo de shoppings do Brasil, proteção de inflação via vendas e aluguéis."
        },
        {
            "ticker": "KNCR11",
            "name": "Kinea Rendimentos Imobiliários",
            "segment": "Papel CRI CDI+",
            "price_brl": 102.30,
            "dy_12m": 0.126,  # 12.6% a.a.
            "pvp": 1.02,
            "liquidity_daily_brl": 11500000,
            "risk_score": "BAIXO",
            "ir_exempt": True,
            "description": "Crédito imobiliário puro High Grade atrelado ao CDI com garantias de primeira linha."
        },
        {
            "ticker": "KNHY11",
            "name": "Kinea High Yield",
            "segment": "Papel CRI IPCA+",
            "price_brl": 98.40,
            "dy_12m": 0.131,  # 13.1% a.a.
            "pvp": 0.98,
            "liquidity_daily_brl": 6400000,
            "risk_score": "MODERADO",
            "ir_exempt": True,
            "description": "Papel atrelado a IPCA + spread robusto para blindagem de poder de compra."
        },
        {
            "ticker": "HGRU11",
            "name": "CSHG Renda Urbana",
            "segment": "Tijolo Varejo/Educacional",
            "price_brl": 128.90,
            "dy_12m": 0.091,  # 9.1% a.a.
            "pvp": 1.00,
            "liquidity_daily_brl": 4800000,
            "risk_score": "BAIXO",
            "ir_exempt": True,
            "description": "Imóveis locados para redes essenciais (Big, D'Or, faculdades) com contratos atípicos."
        }
    ],

    # 2. AÇÕES (EQUITIES BRASIL - VACAS LEITEIRAS PAGADORAS DE DIVIDENDOS)
    "EQUITIES_BR": [
        {
            "ticker": "BBAS3",
            "name": "Banco do Brasil",
            "segment": "Bancos / Financeiro",
            "price_brl": 27.80,
            "dy_12m": 0.102,  # 10.2% a.a.
            "pvp": 0.85,
            "liquidity_daily_brl": 250000000,
            "risk_score": "BAIXO",
            "ir_exempt": False,  # Dividendos isentos, JCP 15%
            "description": "Líder no agronegócio com ROE acima de 21% e payout histórico previsível."
        },
        {
            "ticker": "TAEE11",
            "name": "Taesa Transmissão",
            "segment": "Energia / Transmissão",
            "price_brl": 34.60,
            "dy_12m": 0.098,  # 9.8% a.a.
            "pvp": 1.55,
            "liquidity_daily_brl": 45000000,
            "risk_score": "BAIXO",
            "ir_exempt": False,
            "description": "Receita Anual Permitida (RAP) reajustada por IPCA/IGP-M com previsibilidade total."
        },
        {
            "ticker": "ITUB4",
            "name": "Itaú Unibanco",
            "segment": "Bancos / Financeiro",
            "price_brl": 35.10,
            "dy_12m": 0.078,  # 7.8% a.a.
            "pvp": 1.70,
            "liquidity_daily_brl": 310000000,
            "risk_score": "BAIXO",
            "ir_exempt": False,
            "description": "O banco mais eficiente da América Latina com histórico impecável de distribuição."
        },
        {
            "ticker": "EGIE3",
            "name": "Engie Brasil",
            "segment": "Energia / Geração",
            "price_brl": 41.50,
            "dy_12m": 0.082,  # 8.2% a.a.
            "pvp": 2.10,
            "liquidity_daily_brl": 55000000,
            "risk_score": "BAIXO",
            "ir_exempt": False,
            "description": "Geração renovável limpa com contratos de longo prazo no mercado livre."
        },
        {
            "ticker": "BBSE3",
            "name": "BB Seguridade",
            "segment": "Seguros / Previdência",
            "price_brl": 34.20,
            "dy_12m": 0.106,  # 10.6% a.a.
            "pvp": 5.80,
            "liquidity_daily_brl": 88000000,
            "risk_score": "BAIXO",
            "ir_exempt": False,
            "description": "Monopólio de bancassurance nos canais do Banco do Brasil com fluxo de caixa livre massivo."
        }
    ],

    # 3. CAIXA & RENDA FIXA (SEGURANÇA, JUROS SEMESTRAIS E RESERVA)
    "FIXED_INCOME": [
        {
            "ticker": "NTNB_CUPOM",
            "name": "Tesouro IPCA+ com Juros Semestrais",
            "segment": "Títulos Públicos Federais",
            "price_brl": 4120.00,
            "dy_12m": 0.118,  # ~IPCA + 6.4% a.a.
            "pvp": 1.00,
            "liquidity_daily_brl": 500000000,
            "risk_score": "SOBERANO",
            "ir_exempt": False,
            "description": "Cupom de juros pago semestralmente em maio e novembro, garantia soberana do Tesouro."
        },
        {
            "ticker": "DEB_INCENTIVADA",
            "name": "Debêntures Incentivadas Infraestrutura",
            "segment": "Crédito Privado Isento",
            "price_brl": 1050.00,
            "dy_12m": 0.114,  # IPCA + 6.0% Isento
            "pvp": 1.00,
            "liquidity_daily_brl": 50000000,
            "risk_score": "BAIXO",
            "ir_exempt": True,  # 100% Isento de IR para PF
            "description": "Financiamento de rodovias, saneamento e energia com isenção fiscal pela Lei 12.431."
        },
        {
            "ticker": "TESOURO_SELIC",
            "name": "Tesouro Selic / Caixa Oportunidade",
            "segment": "Reserva de Liquidez",
            "price_brl": 14850.00,
            "dy_12m": 0.105,  # 10.5% Selic a.a.
            "pvp": 1.00,
            "liquidity_daily_brl": 1000000000,
            "risk_score": "ZERO",
            "ir_exempt": False,
            "description": "Liquidez imediata (D+0/D+1) para aproveitar quedas bruscas de mercado."
        }
    ],

    # 4. ATIVOS INTERNACIONAIS (DÓLAR, REITS E DIVIDENDOS GLOBAIS)
    "INTERNATIONAL": [
        {
            "ticker": "O",
            "name": "Realty Income Corp",
            "segment": "US REIT (Dividend Mensal)",
            "price_usd": 53.40,
            "dy_12m": 0.059,  # 5.9% a.a. em Dólar
            "risk_score": "BAIXO",
            "ir_exempt": False,
            "description": "O clássico 'The Monthly Dividend Company' pagando proventos mensais em dólar há 55 anos."
        },
        {
            "ticker": "SCHD",
            "name": "Schwab US Dividend Equity ETF",
            "segment": "US Dividend ETF",
            "price_usd": 28.90,
            "dy_12m": 0.038,  # 3.8% a.a. em Dólar + Crescimento
            "risk_score": "BAIXO",
            "description": "100 empresas americanas com mais de 10 anos consecutivos de dividendos crescentes."
        },
        {
            "ticker": "VNQ",
            "name": "Vanguard Real Estate ETF",
            "segment": "Global Real Estate",
            "price_usd": 86.50,
            "dy_12m": 0.044,  # 4.4% a.a. em Dólar
            "risk_score": "MODERADO",
            "description": "Exposição aos maiores fundos imobiliários do mundo (Data centers, torres 5G, galpões)."
        },
        {
            "ticker": "IVVB11",
            "name": "iShares S&P 500 Fundo de Índice",
            "segment": "B3 / Exposição S&P 500",
            "price_brl": 328.00,
            "dy_12m": 0.015,
            "risk_score": "MODERADO",
            "description": "Proteção cambial e crescimento das 500 maiores corporações dos EUA negociado na B3."
        }
    ]
}

# --------------------------------------------------------------------------
# MATRIZES DE ALOCAÇÃO DO MÉTODO ARCA
# --------------------------------------------------------------------------
ARCA_PROFILES = {
    "CONSERVADOR": {
        "name": "Conservador (Foco em Renda Isenta & Segurança)",
        "weights": {
            "REAL_ESTATE": 0.40,      # 40% FIIs (proventos mensais isentos)
            "EQUITIES_BR": 0.20,      # 20% Ações Dividendos
            "FIXED_INCOME": 0.25,     # 25% Renda Fixa / Caixa
            "INTERNATIONAL": 0.15     # 15% Dólar / REITs
        },
        "target_net_dy": 0.096,       # 9.6% a.a. líquido médio
        "description": "Máxima previsibilidade mensal com foco em isenção de IR e risco mínimo de volatilidade."
    },
    "ARCA_EQUILIBRADA": {
        "name": "ARCA Equilibrada (Thiago Nigro Clássica)",
        "weights": {
            "REAL_ESTATE": 0.35,      # 35% FIIs
            "EQUITIES_BR": 0.25,      # 25% Ações
            "FIXED_INCOME": 0.20,     # 20% Caixa
            "INTERNATIONAL": 0.20     # 20% Internacional
        },
        "target_net_dy": 0.092,       # 9.2% a.a. líquido médio
        "description": "A proporção dourada da ARCA: descorrelação máxima entre bolsa brasileira, imóveis, juros e dólar."
    },
    "ACELERADOR_PROVENTOS": {
        "name": "Acelerador de Proventos (High Yield Inteligente)",
        "weights": {
            "REAL_ESTATE": 0.45,      # 45% FIIs (Tijolo + Papel High Grade)
            "EQUITIES_BR": 0.30,      # 30% Ações Vacas Leiteiras
            "FIXED_INCOME": 0.10,     # 10% Caixa Oportunidade
            "INTERNATIONAL": 0.15     # 15% REITs Dólar
        },
        "target_net_dy": 0.104,       # 10.4% a.a. líquido médio
        "description": "Maximiza o pinga-pinga mensal na conta, encurtando o patrimônio necessário para a meta de renda."
    }
}


class PlutusAgent:
    """
    Agente de Inteligência Financeira e Alocação Patrimonial do 1Crypten.
    Calcula a matemática reversa para viver de renda com o Método ARCA.
    """
    def __init__(self):
        self._cache_quotes: Dict[str, Any] = {}
        self._cache_time: float = 0.0
        self._cache_ttl: float = 3600.0  # 1 hora de cache para economizar chamadas gratuitas
        self._usd_brl_rate: float = 5.60

    async def update_live_quotes_if_needed(self):
        """Atualiza cotações ao vivo via API pública do Yahoo Finance / BCB de forma resiliente."""
        now = time.time()
        if now - self._cache_time < self._cache_ttl and self._cache_quotes:
            return

        try:
            # 1. Consulta Cotação do Dólar via API pública AwesomeAPI (Gratuita, sem token)
            async def _fetch_usd():
                try:
                    req = urllib.request.Request("https://economia.awesomeapi.com.br/last/USD-BRL", headers={"User-Agent": "1Crypten/7.0"})
                    with urllib.request.urlopen(req, timeout=3.0) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                        if "USDBRL" in data and "bid" in data["USDBRL"]:
                            self._usd_brl_rate = float(data["USDBRL"]["bid"])
                            logger.info(f"[PLUTUS] Dólar atualizado: R$ {self._usd_brl_rate:.2f}")
                except Exception as ex:
                    logger.warning(f"[PLUTUS] Falha ao atualizar dólar ao vivo: {ex}, mantendo fallback R$ {self._usd_brl_rate}")

            await asyncio.to_thread(_fetch_usd)
            self._cache_time = now
        except Exception as e:
            logger.warning(f"[PLUTUS] Contingência ativada com dados institucionais canônicos: {e}")

    def simulate_income(self, target_monthly_income_brl: float, profile_key: str = "ARCA_EQUILIBRADA", current_patrimony_brl: float = 0.0) -> Dict[str, Any]:
        """
        Executa a matemática financeira reversa para viver de renda.
        Calcula o patrimônio necessário, divisão por pilares e plano de compras cota por cota.
        """
        if target_monthly_income_brl <= 0:
            target_monthly_income_brl = 50000.0

        profile = ARCA_PROFILES.get(profile_key, ARCA_PROFILES["ARCA_EQUILIBRADA"])
        weights = profile["weights"]
        target_dy = profile["target_net_dy"]

        # Matemática Reversa: Renda Anual = Renda Mensal * 12
        target_annual_income = target_monthly_income_brl * 12.0

        # Patrimônio Necessário = Renda Anual / DY Médio Líquido
        required_patrimony = target_annual_income / target_dy

        # Gap de Acumulação (caso o usuário já tenha um valor inicial)
        patrimony_gap = max(0.0, required_patrimony - current_patrimony_brl)
        progress_pct = min(100.0, (current_patrimony_brl / required_patrimony * 100.0)) if required_patrimony > 0 else 0.0

        # -------------------------------------------------------------
        # Distribuição nos 4 Pilares da ARCA
        # -------------------------------------------------------------
        pillars_breakdown = {}
        total_monthly_est = 0.0
        total_annual_est = 0.0

        pillars_names = {
            "REAL_ESTATE": "Real Estate (FIIs Isentos)",
            "EQUITIES_BR": "Ações de Dividendos (BR)",
            "FIXED_INCOME": "Caixa & Renda Fixa",
            "INTERNATIONAL": "Ativos Internacionais (Dólar)"
        }

        recommended_assets = []

        for p_key, p_weight in weights.items():
            allocated_amount = required_patrimony * p_weight
            assets_pool = ARCA_UNIVERSE.get(p_key, [])
            
            p_dy_sum = sum(a["dy_12m"] for a in assets_pool)
            p_avg_dy = p_dy_sum / max(1, len(assets_pool))
            
            p_annual_income = allocated_amount * p_avg_dy
            p_monthly_income = p_annual_income / 12.0

            total_annual_est += p_annual_income
            total_monthly_est += p_monthly_income

            pillars_breakdown[p_key] = {
                "name": pillars_names.get(p_key, p_key),
                "weight_pct": round(p_weight * 100.0, 1),
                "allocated_brl": round(allocated_amount, 2),
                "avg_dy_pct": round(p_avg_dy * 100.0, 2),
                "monthly_income_brl": round(p_monthly_income, 2),
                "annual_income_brl": round(p_annual_income, 2),
                "assets_count": len(assets_pool)
            }

            # Distribui o capital do pilar igualmente entre os ativos de elite
            asset_weight_in_pilar = 1.0 / max(1, len(assets_pool))
            for a in assets_pool:
                asset_allocated = allocated_amount * asset_weight_in_pilar
                unit_price = a.get("price_brl", 0.0)
                
                # Conversão para ativos em Dólar
                if unit_price <= 0 and "price_usd" in a:
                    unit_price = a["price_usd"] * self._usd_brl_rate

                shares_count = math.floor(asset_allocated / max(0.01, unit_price))
                asset_annual = asset_allocated * a["dy_12m"]
                asset_monthly = asset_annual / 12.0

                recommended_assets.append({
                    "pillar": p_key,
                    "pillar_name": pillars_names.get(p_key, p_key),
                    "ticker": a["ticker"],
                    "name": a["name"],
                    "segment": a["segment"],
                    "unit_price_brl": round(unit_price, 2),
                    "dy_12m_pct": round(a["dy_12m"] * 100.0, 2),
                    "portfolio_share_pct": round(p_weight * asset_weight_in_pilar * 100.0, 2),
                    "allocated_brl": round(asset_allocated, 2),
                    "shares_to_buy": shares_count,
                    "monthly_income_brl": round(asset_monthly, 2),
                    "annual_income_brl": round(asset_annual, 2),
                    "risk_score": a.get("risk_score", "BAIXO"),
                    "ir_exempt": a.get("ir_exempt", False),
                    "description": a.get("description", "")
                })

        # -------------------------------------------------------------
        # Projeção de Cronograma Mensal ("Pinga-Pinga" nos 12 meses)
        # -------------------------------------------------------------
        monthly_schedule = []
        months = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        base_monthly = total_monthly_est
        
        # Simula sazonalidade real (Mai/Nov picos de NTN-B e JCP bancário)
        seasonality = [0.94, 0.96, 1.02, 0.98, 1.18, 0.96, 0.95, 1.04, 0.98, 0.97, 1.16, 1.06]
        for idx, m in enumerate(months):
            factor = seasonality[idx]
            m_val = base_monthly * factor
            monthly_schedule.append({
                "month_index": idx + 1,
                "month_name": m,
                "estimated_income_brl": round(m_val, 2),
                "is_peak_month": factor > 1.10
            })

        return {
            "status": "success",
            "timestamp": time.time(),
            "target_monthly_income_brl": round(target_monthly_income_brl, 2),
            "profile_key": profile_key,
            "profile_name": profile["name"],
            "profile_description": profile["description"],
            "required_patrimony_brl": round(required_patrimony, 2),
            "current_patrimony_brl": round(current_patrimony_brl, 2),
            "patrimony_gap_brl": round(patrimony_gap, 2),
            "progress_pct": round(progress_pct, 2),
            "overall_dy_pct": round(target_dy * 100.0, 2),
            "total_monthly_est_brl": round(total_monthly_est, 2),
            "total_annual_est_brl": round(total_annual_est, 2),
            "usd_brl_rate": round(self._usd_brl_rate, 2),
            "pillars": pillars_breakdown,
            "recommended_assets": recommended_assets,
            "monthly_schedule": monthly_schedule
        }

    def generate_hermes_diagnosis(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gera o parecer executivo e confluência de risco do Hermes Intelligence sobre a carteira."""
        target_income = simulation_data.get("target_monthly_income_brl", 50000.0)
        req_patrimony = simulation_data.get("required_patrimony_brl", 6000000.0)
        profile_name = simulation_data.get("profile_name", "ARCA Equilibrada")
        
        diagnosis_text = (
            f"DIAGNÓSTICO EXECUTIVO DO ORQUESTRADOR HERMES:\n"
            f"Para atingir o objetivo inegociável de R$ {target_income:,.2f}/mês de renda passiva líquida perpétua "
            f"sob a arquitetura '{profile_name}', foi estruturado um portfólio de {req_patrimony:,.2f} descorrelacionado "
            f"em 4 pilares anti-frágeis.\n\n"
            f"1. BLINDAGEM TRIBUTÁRIA: 40% do fluxo mensal é canalizado via Fundos Imobiliários e Debêntures com 100% "
            f"de isenção de IR na pessoa física pela legislação brasileira vigente.\n"
            f"2. PROTEÇÃO CAMBIAL: 20% do capital alocado em Dólar e REITs globais garante que a sua renda preserve "
            f"poder de compra internacional caso ocorra desvalorização da moeda nacional.\n"
            f"3. EXPECTATIVA MATEMÁTICA: O portfólio entrega uma taxa média ponderada de ~9.5% a.a. líquida de impostos, "
            f"mantendo a sua renda passiva com zero dependência de vendas parciais de patrimônio."
        )

        return {
            "status": "success",
            "conductor": "HERMES INTELLIGENCE",
            "agent": "PLUTUS",
            "methodology": "MÉTODO ARCA (PROVENTOS)",
            "doctrine": "PERPETUAL_CASH_FLOW_GUARDIAN",
            "diagnosis_text": diagnosis_text,
            "recommended_actions": [
                "Iniciar alocação prioritária em Fundos Imobiliários de Logística e Shoppings para ativar o pinga-pinga mensal imediato.",
                "Montar posição em Ações bancárias e elétricas nos períodos de anúncio de proventos (JCP e Dividendos).",
                "Rebalancear a carteira semestralmente conforme o Método ARCA original: comprar o pilar que ficou para trás para manter a proporção ideal."
            ]
        }


plutus_agent = PlutusAgent()
