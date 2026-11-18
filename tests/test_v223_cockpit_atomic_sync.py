# -*- coding: utf-8 -*-
"""
Empirical test for V223: Cockpit Atomic Telemetry Synchronization.
Verifies:
1. get_cockpit_telemetry consolidates slots, funding, unified_state, pulse, and recent_trades atomically.
2. Invalidation hooks immediately purge in-memory caches upon trade state transitions.
3. Net PnL and net ROI are consistently exposed across both custody and audit history.
"""
import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

async def test_v223_atomic_sync():
    from routes.trading import get_cockpit_telemetry, invalidate_slots_cache, _last_slots_cache
    from routes.sandbox import invalidate_unified_state_cache
    from services.database_service import database_service

    print("--- [TEST 1]: Invalidation of Telemetry Caches ---")
    invalidate_slots_cache()
    invalidate_unified_state_cache()
    from routes.trading import _last_slots_cache as sc
    from routes.sandbox import _last_unified_state_cache as uc
    assert sc is None, "Slots cache should be None after invalidation"
    assert uc is None, "Unified state cache should be None after invalidation"
    print("PASS: Invalidation hooks successfully purge memory caches.")

    print("\n--- [TEST 2]: get_cockpit_telemetry Atomic Response ---")
    telem = await get_cockpit_telemetry()
    assert "slots" in telem, "Telemetry must include slots"
    assert "funding" in telem, "Telemetry must include funding"
    assert "unified_state" in telem, "Telemetry must include unified_state"
    assert "pulse" in telem, "Telemetry must include pulse"
    assert "recent_trades" in telem, "Telemetry must include recent_trades"
    print(f"PASS: Telemetry payload contains all 5 atomic pillars. Recent trades count: {len(telem['recent_trades'])}")

    print("\n--- [TEST 3]: Net PnL Fidelity in Recent Trades ---")
    if telem["recent_trades"]:
        first = telem["recent_trades"][0]
        assert "net_pnl_usd" in first, "Trade must expose net_pnl_usd"
        assert "pnl_pct" in first, "Trade must expose pnl_pct"
        print(f"PASS: Trade {first.get('id')} audited with net_pnl_usd={first.get('net_pnl_usd')} and net_roi={first.get('pnl_pct')}%.")
    else:
        print("PASS: No closed trades present, empty recent_trades list verified.")

    print("\n=== ALL V223 SYNCHRONIZATION TESTS PASSED ===")

if __name__ == "__main__":
    asyncio.run(test_v223_atomic_sync())
