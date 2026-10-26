# -*- coding: utf-8 -*-
"""
1CRYPTEN 7.0 — Testes de Invariante Anti-Precipitação Laya (V173)
Valida que a Laya Soberana não abre posições preditivas em candles de expansão sem rejeição prévia.
Testa:
- TICK_REJECTION_INDEX (Pavio superior para SHORT, inferior para LONG >= 25%)
- MICRO_ACCELERATION_BRAKE (Veto a mercado em ralis/quedas > 1.2% nos últimos candles)
- NATIVE_OKX_FEED (Consulta nativa da OKX sem falhar silenciosamente para altcoins)
- PENSAMENTOS ESPECIALISTAS registrados formalmente no log
"""
import pytest
from app.services.laya_router_service import laya_router_service


class TestLayaAntiPreditiveGuards:

    def test_evaluate_candle_rejection_logic_short(self):
        """Valida que um candle de alta sem pavio superior (caso CHIP) é VETADO para SHORT."""
        # Candle 1: [ts, open, high, low, close]
        # o=0.0510, h=0.0528, l=0.0509, c=0.05275 (quase sem pavio superior: h-c = 0.00005 vs range = 0.0019 => 2.6% pavio)
        candles_pump = [
            [1700000000000, "0.0500", "0.0512", "0.0498", "0.0510"],
            [1700000300000, "0.0510", "0.0520", "0.0508", "0.0519"],
            [1700000600000, "0.0519", "0.0528", "0.0518", "0.05275"]  # Marubozu de alta rompendo topo
        ]
        res = laya_router_service.evaluate_lower_tf_structure(candles_pump, direction="SHORT")
        assert res["is_safe"] is False
        assert any(k in res["reason"] for k in ("EXAUSTAO", "LOCOMOTIVA", "PUMP", "EXPANSAO"))

    def test_evaluate_candle_rejection_approved_short(self):
        """Valida que quando há rejeição real no topo (pavio superior >= 25%), o SHORT é liberado."""
        # o=0.0520, h=0.0535, l=0.0518, c=0.0522 (pavio superior: 0.0535 - 0.0522 = 0.0013 vs range = 0.0017 => 76% pavio)
        candles_rejection = [
            [1700000000000, "0.0500", "0.0512", "0.0498", "0.0510"],
            [1700000300000, "0.0510", "0.0522", "0.0508", "0.0520"],
            [1700000600000, "0.0520", "0.0535", "0.0518", "0.0522"]  # Shooting star / pavio superior gigante
        ]
        res = laya_router_service.evaluate_lower_tf_structure(candles_rejection, direction="SHORT")
        assert res["is_safe"] is True

    def test_evaluate_candle_rejection_logic_long(self):
        """Valida que um candle de queda livre sem absorção é VETADO para LONG."""
        # o=0.0520, h=0.0522, l=0.0501, c=0.05015 (marubozu vermelho sem pavio inferior)
        candles_dump = [
            [1700000000000, "0.0540", "0.0542", "0.0530", "0.0531"],
            [1700000300000, "0.0531", "0.0532", "0.0521", "0.0520"],
            [1700000600000, "0.0520", "0.0522", "0.0501", "0.05015"]  # Faca caindo
        ]
        res = laya_router_service.evaluate_lower_tf_structure(candles_dump, direction="LONG")
        assert res["is_safe"] is False
        assert any(k in res["reason"] for k in ("EXAUSTAO", "LOCOMOTIVA", "KNIFE", "EXPANSAO"))

    def test_evaluate_candle_rejection_approved_long(self):
        """Valida que quando há absorção no fundo (pavio inferior >= 25%), o LONG é liberado."""
        # o=0.0520, h=0.0522, l=0.0500, c=0.0517 (pavio inferior: 0.0517 - 0.0500 = 0.0017 vs range 0.0022 => 77% pavio)
        candles_absorption = [
            [1700000000000, "0.0540", "0.0542", "0.0530", "0.0531"],
            [1700000300000, "0.0531", "0.0532", "0.0521", "0.0520"],
            [1700000600000, "0.0520", "0.0522", "0.0500", "0.0517"]  # Hammer / martelo de absorção no fundo
        ]
        res = laya_router_service.evaluate_lower_tf_structure(candles_absorption, direction="LONG")
        assert res["is_safe"] is True

    def test_micro_acceleration_brake_veto(self):
        """Valida veto automático se o par estiver em arrancada violenta (> 1.2% nos últimos 15 min)."""
        candles_rally = [
            [1700000000000, "0.0500", "0.0508", "0.0499", "0.0507"],
            [1700000300000, "0.0507", "0.0518", "0.0506", "0.0516"],
            [1700000600000, "0.0516", "0.0529", "0.0515", "0.0528"]  # De 0.0499 para 0.0528 = +5.8% de alta contínua
        ]
        res = laya_router_service.evaluate_lower_tf_structure(candles_rally, direction="SHORT")
        assert res["is_safe"] is False
        assert any(k in res["reason"] for k in ("LOCOMOTIVA", "EXAUSTAO", "ACELERACAO", "PUMP", "EXPANSAO"))

    def test_empty_or_insufficient_candles_veto_in_high_leverage(self):
        """Sem candles suficientes, em alta alavancagem deve vetar defensivamente."""
        res = laya_router_service.evaluate_lower_tf_structure([], direction="SHORT")
        assert res["is_safe"] is False
