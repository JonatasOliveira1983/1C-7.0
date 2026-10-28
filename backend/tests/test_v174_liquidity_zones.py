# -*- coding: utf-8 -*-
"""
1CRYPTEN 7.0 — Testes de Ciclo de Liquidez em 3 Zonas (Metodologia Encryptos V174)
Valida a classificação determinística das 3 zonas de distância:
- ZONA 1 (HUNT): Distância >= 1.5% -> Entrada a favor do ímã permitida
- ZONA 2 (DEAD_ZONE): 0.3% <= Distância < 1.5% -> Veto de entrada (risco de topo/fundo)
- ZONA 3 (EXHAUSTION): Distância < 0.3% -> Gatilho de reversão / Sweep pós-absorção
"""
import pytest
from app.services.coinglass_heatmap_service import coinglass_heatmap_service


class TestLiquidityZonesEncryptos:

    def test_classify_lifecycle_hunt_zone(self):
        """Valida que distância >= 1.5% qualifica como HUNT com entrada a favor permitida."""
        current_price = 100.0
        target_price = 103.5  # 3.5% de distância
        magnet = "BULLISH_SWEEP"

        lifecycle = coinglass_heatmap_service.classify_liquidity_lifecycle(
            current_price=current_price,
            target_price=target_price,
            magnet_direction=magnet
        )

        assert lifecycle["zone_id"] == "HUNT"
        assert lifecycle["action_allowed"] == "ENTRY_FAVOR"
        assert "LONG" in lifecycle["action_label"]
        assert lifecycle["distance_pct"] == 3.5
        assert lifecycle["zone_color"] == "#00E676"

    def test_classify_lifecycle_dead_zone_veto(self):
        """Valida que distância entre 0.3% e 1.5% aciona VETO na ZONA MORTA."""
        current_price = 100.0
        target_price = 100.8  # 0.8% de distância
        magnet = "BULLISH_SWEEP"

        lifecycle = coinglass_heatmap_service.classify_liquidity_lifecycle(
            current_price=current_price,
            target_price=target_price,
            magnet_direction=magnet
        )

        assert lifecycle["zone_id"] == "DEAD_ZONE"
        assert lifecycle["action_allowed"] == "VETO_ENTRY"
        assert "VETO" in lifecycle["action_label"]
        assert lifecycle["distance_pct"] == 0.8
        assert lifecycle["zone_color"] == "#FFD600"

    def test_classify_lifecycle_exhaustion_sweep(self):
        """Valida que distância < 0.3% qualifica como ZONA DE EXAUSTÃO / SWEEP."""
        current_price = 100.0
        target_price = 100.1  # 0.1% de distância (bolsão atingido)
        magnet = "BULLISH_SWEEP"

        lifecycle = coinglass_heatmap_service.classify_liquidity_lifecycle(
            current_price=current_price,
            target_price=target_price,
            magnet_direction=magnet
        )

        assert lifecycle["zone_id"] == "EXHAUSTION"
        assert lifecycle["action_allowed"] == "REVERSAL_TRIGGER"
        assert "REVERSÃO" in lifecycle["action_label"]
        assert lifecycle["distance_pct"] == 0.1
        assert lifecycle["zone_color"] == "#00F0FF"

    def test_bearish_sweep_direction_action(self):
        """Valida que em BEARISH_SWEEP na zona HUNT, a ação recomendada é SHORT."""
        current_price = 100.0
        target_price = 97.0  # 3.0% abaixo
        magnet = "BEARISH_SWEEP"

        lifecycle = coinglass_heatmap_service.classify_liquidity_lifecycle(
            current_price=current_price,
            target_price=target_price,
            magnet_direction=magnet
        )

        assert lifecycle["zone_id"] == "HUNT"
        assert lifecycle["action_allowed"] == "ENTRY_FAVOR"
        assert "SHORT" in lifecycle["action_label"]
        assert lifecycle["distance_pct"] == 3.0

    @pytest.mark.asyncio
    async def test_get_liquidity_heatmap_includes_lifecycle(self):
        """Garante que a resposta do serviço contenha o bloco lifecycle completo."""
        res = await coinglass_heatmap_service.get_liquidity_heatmap("SOLUSDT", current_price=150.0)
        assert "lifecycle" in res
        lifecycle = res["lifecycle"]
        assert lifecycle["zone_id"] in ("HUNT", "DEAD_ZONE", "EXHAUSTION")
        assert "zone_label" in lifecycle
        assert "action_allowed" in lifecycle
        assert "distance_pct" in lifecycle
        assert "hunt_bound" in lifecycle
        assert "dead_bound" in lifecycle
        assert "exhaustion_bound" in lifecycle
        assert "target_region" in lifecycle
        assert lifecycle["target_region"] in ("ACIMA", "ABAIXO")
        assert "target_region_label" in lifecycle
        assert "target_volume_usd" in res
        assert "target_region" in res
        assert res["target_region"] in ("ACIMA", "ABAIXO")
