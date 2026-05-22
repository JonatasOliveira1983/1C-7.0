# -*- coding: utf-8 -*-
"""
📊 Trade Analyst V1.0 - Performance Intelligence Agent
========================================================
Learns from every trade to improve system profitability over time.

Capabilities:
- Post-trade autopsy (why did it win/lose?)
- Pattern win-rate tracking
- Session performance analysis (Asia/London/NY)
- Target accuracy calibration
- Adaptive threshold recommendations

Author: Antigravity AI
Version: 1.0
"""

import logging
import asyncio
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from services.agents.aios_adapter import AIOSAgent

logger = logging.getLogger("TradeAnalyst")

# Session boundaries (UTC)
SESSIONS = {
    "asia":    {"start": 0,  "end": 8},    # 00:00-08:00 UTC
    "london":  {"start": 8,  "end": 16},   # 08:00-16:00 UTC
    "ny":      {"start": 13, "end": 22},   # 13:00-22:00 UTC (overlaps London)
}


def _get_session(utc_hour: int) -> str:
    """Determines the trading session based on UTC hour."""
    if 0 <= utc_hour < 8:
        return "asia"
    elif 8 <= utc_hour < 13:
        return "london"
    elif 13 <= utc_hour < 22:
        return "ny"
    else:
        return "asia"  # Late night = Asia pre-open


def _classify_result(pnl: float, pnl_pct: float) -> str:
    """Classifies trade result with granularity beyond win/loss."""
    if pnl_pct >= 50.0:
        return "big_win"        # 50%+ ROI
    elif pnl_pct >= 10.0:
        return "win"            # 10-50% ROI
    elif pnl_pct >= 0:
        return "breakeven"      # 0-10% ROI (marginal)
    elif pnl_pct >= -20.0:
        return "small_loss"     # -20 to 0% ROI
    else:
        return "big_loss"       # < -20% ROI


class TradeAnalyst(AIOSAgent):
    """
    Performance Intelligence Agent.
    Analyzes every closed trade and builds a knowledge base
    that feeds back into signal generation quality.
    """

    def __init__(self):
        super().__init__(
            agent_id="trade_analyst_v1",
            role="TradeAnalyst",
            capabilities=["trade_autopsy", "pattern_scoring", "session_analysis", "target_calibration"]
        )
        self.analysis_interval = 1800  # 30 minutes
        self._cache: Dict[str, Any] = {}
        self._initialized = False

    async def on_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """AIOS interface — handles TRADE_CLOSED messages."""
        msg_type = message.get("type", "")
        if msg_type == "TRADE_CLOSED":
            trade_data = message.get("data", {})
            await self.analyze_closed_trade(trade_data)
            return {"status": "analyzed", "symbol": trade_data.get("symbol")}
        elif msg_type == "GET_ANALYTICS":
            return await self.get_analytics_summary()
        return {"status": "ignored", "reason": f"Unknown message type: {msg_type}"}

    # ================================================================
    # CORE: Post-Trade Autopsy
    # ================================================================

    async def analyze_closed_trade(self, trade_data: Dict[str, Any]):
        """
        Called after each trade closure. Performs post-mortem analysis
        and records enriched autopsy to Firebase.
        """
        try:
            from services.firebase_service import firebase_service

            symbol = trade_data.get("symbol") or "UNKNOWN"
            side = trade_data.get("side") or "Buy"
            entry_price = float(trade_data.get("entry_price") or 0)
            exit_price = float(trade_data.get("exit_price") or 0)
            pnl = float(trade_data.get("pnl") or 0)
            pnl_pct = float(trade_data.get("pnl_percent") or 0)
            close_reason = trade_data.get("close_reason") or "UNKNOWN"
            pattern = trade_data.get("pattern") or "unknown"
            slot_type = trade_data.get("slot_type") or "TREND"
            structural_target = float(trade_data.get("structural_target") or 0)
            opened_at = trade_data.get("opened_at") or 0

            # Calculate ROI if not provided
            if pnl_pct == 0 and entry_price > 0 and exit_price > 0:
                side_norm = (side or "").lower()
                if side_norm == "buy":
                    pnl_pct = ((exit_price - entry_price) / entry_price) * 50 * 100  # 50x leverage
                else:
                    pnl_pct = ((entry_price - exit_price) / entry_price) * 50 * 100

            # Determine session
            now = datetime.now(timezone.utc)
            session = _get_session(now.hour)
            
            # If opened_at is available, use entry time for session
            if opened_at and opened_at > 0:
                try:
                    entry_time = datetime.fromtimestamp(opened_at / 1000 if opened_at > 1e12 else opened_at, tz=timezone.utc)
                    session = _get_session(entry_time.hour)
                except Exception:
                    pass

            # Calculate duration
            duration_minutes = 0
            if opened_at and opened_at > 0:
                try:
                    opened_ts = opened_at / 1000 if opened_at > 1e12 else opened_at
                    duration_minutes = (time.time() - opened_ts) / 60
                except Exception:
                    pass

            # Determine SL phase from close reason
            sl_phase = "UNKNOWN"
            for phase in ["MEGA_PULSE", "PROFIT_LOCK", "FLASH_SECURE", "STABILIZE", "RISK_ZERO", "SAFE", "HARD_STOP"]:
                if phase in (close_reason or "").upper():
                    sl_phase = phase
                    break
            
            # Target accuracy
            target_hit = False
            target_accuracy_pct = 0
            if structural_target > 0 and entry_price > 0:
                side_norm = (side or "").lower()
                if side_norm == "buy":
                    target_distance = structural_target - entry_price
                    actual_distance = exit_price - entry_price
                else:
                    target_distance = entry_price - structural_target
                    actual_distance = entry_price - exit_price
                
                if target_distance > 0:
                    target_accuracy_pct = (actual_distance / target_distance) * 100
                    target_hit = target_accuracy_pct >= 90  # 90%+ = target hit

            # Classification
            result = _classify_result(pnl, pnl_pct)

            # Build autopsy document
            autopsy = {
                "symbol": symbol,
                "side": side,
                "slot_type": slot_type,
                "pattern": pattern,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "pnl_usd": pnl,
                "pnl_pct": round(pnl_pct, 2),
                "result": result,
                "is_win": pnl >= 0,
                "close_reason": close_reason,
                "sl_phase_at_close": sl_phase,
                "session": session,
                "duration_minutes": round(duration_minutes, 1),
                "structural_target": structural_target,
                "target_hit": target_hit,
                "target_accuracy_pct": round(target_accuracy_pct, 1),
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Persist to Firebase
            await asyncio.to_thread(
                firebase_service.db.collection("trade_analytics").add, autopsy
            )

            # Update aggregated summary
            await self._update_aggregated_summary(autopsy)

            emoji = "✅" if pnl >= 0 else "❌"
            logger.info(
                f"📊 [AUTOPSY] {emoji} {symbol} | {result} | "
                f"ROI={pnl_pct:.1f}% | Pattern={pattern} | "
                f"Session={session} | Phase={sl_phase} | "
                f"Target={'HIT' if target_hit else f'{target_accuracy_pct:.0f}%'}"
            )

        except Exception as e:
            logger.error(f"TradeAnalyst autopsy error: {e}")

    # ================================================================
    # AGGREGATED SUMMARY (Pattern Scores, Sessions, Targets)
    # ================================================================

    async def _update_aggregated_summary(self, autopsy: Dict[str, Any]):
        """Incrementally updates the aggregated analytics summary."""
        try:
            from services.firebase_service import firebase_service

            summary = await self._get_or_create_summary()

            # 1. Update pattern scores
            pattern = autopsy.get("pattern", "unknown")
            if pattern not in summary["pattern_scores"]:
                summary["pattern_scores"][pattern] = {"wins": 0, "losses": 0, "total_roi": 0, "count": 0}

            ps = summary["pattern_scores"][pattern]
            ps["count"] += 1
            ps["total_roi"] += autopsy.get("pnl_pct", 0)
            if autopsy.get("is_win"):
                ps["wins"] += 1
            else:
                ps["losses"] += 1

            # 2. Update session performance
            session = autopsy.get("session", "unknown")
            if session not in summary["session_performance"]:
                summary["session_performance"][session] = {"wins": 0, "losses": 0, "total_pnl": 0, "count": 0}

            sp = summary["session_performance"][session]
            sp["count"] += 1
            sp["total_pnl"] += autopsy.get("pnl_usd", 0)
            if autopsy.get("is_win"):
                sp["wins"] += 1
            else:
                sp["losses"] += 1

            # 3. Update target accuracy
            ta = summary["target_accuracy"]
            ta["total_trades"] = ta.get("total_trades", 0) + 1
            ta["total_target_accuracy"] = ta.get("total_target_accuracy", 0) + autopsy.get("target_accuracy_pct", 0)
            if autopsy.get("target_hit"):
                ta["targets_hit"] = ta.get("targets_hit", 0) + 1

            # 4. Update close phase distribution
            phase = autopsy.get("sl_phase_at_close", "UNKNOWN")
            cpd = summary["close_phase_distribution"]
            cpd[phase] = cpd.get(phase, 0) + 1

            # 5. Calculate adaptive config
            summary["adaptive_config"] = self._calculate_adaptive_config(summary)
            summary["updated_at"] = datetime.now(timezone.utc).isoformat()

            # Persist
            await asyncio.to_thread(
                firebase_service.db.collection("trade_analytics").document("summary").set,
                summary
            )

            self._cache = summary

        except Exception as e:
            logger.error(f"TradeAnalyst summary update error: {e}")

    async def _get_or_create_summary(self) -> Dict[str, Any]:
        """Gets or creates the aggregated analytics summary."""
        # Use cache if fresh (< 5 min)
        if self._cache and self._cache.get("updated_at"):
            try:
                cached_time = datetime.fromisoformat(self._cache["updated_at"])
                if (datetime.now(timezone.utc) - cached_time) < timedelta(minutes=5):
                    return self._cache
            except Exception:
                pass

        try:
            from services.firebase_service import firebase_service
            doc = await asyncio.to_thread(
                firebase_service.db.collection("trade_analytics").document("summary").get
            )
            if doc.exists:
                summary = doc.to_dict()
                self._cache = summary
                return summary
        except Exception as e:
            logger.warning(f"Could not fetch analytics summary: {e}")

        # Create default
        return {
            "pattern_scores": {},
            "session_performance": {},
            "target_accuracy": {
                "total_trades": 0,
                "total_target_accuracy": 0,
                "targets_hit": 0,
            },
            "close_phase_distribution": {},
            "adaptive_config": {
                "min_score_adjustment": 0,
                "blocked_patterns": [],
                "preferred_session": "any",
                "overall_win_rate": 0,
            },
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _calculate_adaptive_config(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates adaptive configuration based on accumulated data."""
        config = {
            "min_score_adjustment": 0,
            "blocked_patterns": [],
            "preferred_session": "any",
            "overall_win_rate": 0,
        }

        # Overall win rate
        total_wins = 0
        total_trades = 0
        for ps in summary.get("pattern_scores", {}).values():
            total_wins += ps.get("wins", 0)
            total_trades += ps.get("count", 0)

        if total_trades > 0:
            config["overall_win_rate"] = round((total_wins / total_trades) * 100, 1)

            # If win rate < 45% after 20+ trades, increase min_score
            if total_trades >= 20 and config["overall_win_rate"] < 45:
                config["min_score_adjustment"] = 5
            elif total_trades >= 20 and config["overall_win_rate"] < 40:
                config["min_score_adjustment"] = 10

        # Block patterns with < 35% win rate (min 5 trades)
        for pattern, ps in summary.get("pattern_scores", {}).items():
            count = ps.get("count", 0)
            wins = ps.get("wins", 0)
            if count >= 5 and (wins / count) < 0.35:
                config["blocked_patterns"].append(pattern)

        # Identify best session
        best_session = "any"
        best_wr = 0
        for session, sp in summary.get("session_performance", {}).items():
            count = sp.get("count", 0)
            wins = sp.get("wins", 0)
            if count >= 5:
                wr = wins / count
                if wr > best_wr:
                    best_wr = wr
                    best_session = session

        config["preferred_session"] = best_session
        return config

    # ================================================================
    # PUBLIC API: Analytics Summary
    # ================================================================

    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Returns the complete analytics summary for the API endpoint."""
        summary = await self._get_or_create_summary()

        # Enrich with computed fields
        result = {
            "pattern_scores": {},
            "session_performance": {},
            "target_accuracy": {},
            "close_phase_distribution": summary.get("close_phase_distribution", {}),
            "adaptive_config": summary.get("adaptive_config", {}),
            "updated_at": summary.get("updated_at", ""),
        }

        # Compute win rates for patterns
        for pattern, ps in summary.get("pattern_scores", {}).items():
            count = ps.get("count", 0)
            wins = ps.get("wins", 0)
            avg_roi = ps.get("total_roi", 0) / count if count > 0 else 0
            result["pattern_scores"][pattern] = {
                "wins": wins,
                "losses": ps.get("losses", 0),
                "count": count,
                "win_rate": round((wins / count * 100) if count > 0 else 0, 1),
                "avg_roi": round(avg_roi, 1),
            }

        # Compute win rates for sessions
        for session, sp in summary.get("session_performance", {}).items():
            count = sp.get("count", 0)
            wins = sp.get("wins", 0)
            avg_pnl = sp.get("total_pnl", 0) / count if count > 0 else 0
            result["session_performance"][session] = {
                "wins": wins,
                "losses": sp.get("losses", 0),
                "count": count,
                "win_rate": round((wins / count * 100) if count > 0 else 0, 1),
                "avg_pnl_usd": round(avg_pnl, 2),
            }

        # Target accuracy
        ta = summary.get("target_accuracy", {})
        total = ta.get("total_trades", 0)
        result["target_accuracy"] = {
            "total_trades": total,
            "avg_target_accuracy_pct": round(ta.get("total_target_accuracy", 0) / total, 1) if total > 0 else 0,
            "targets_hit": ta.get("targets_hit", 0),
            "target_hit_rate": round((ta.get("targets_hit", 0) / total * 100) if total > 0 else 0, 1),
        }

        return result

    # ================================================================
    # BACKGROUND LOOP: Periodic Batch Analysis
    # ================================================================

    async def start_loop(self):
        """Background loop: scans for unanalyzed trades every 30 minutes."""
        logger.info("📊 TradeAnalyst loop started (30min interval)")
        await asyncio.sleep(60)  # Initial delay

        while True:
            try:
                await self._batch_analyze_recent_trades()
            except Exception as e:
                logger.error(f"TradeAnalyst loop error: {e}")

            await asyncio.sleep(self.analysis_interval)

    async def _batch_analyze_recent_trades(self):
        """Scans trade_history for trades not yet in trade_analytics."""
        try:
            from services.firebase_service import firebase_service

            # Get recent trades
            trades = await firebase_service.get_trade_history(limit=20)
            if not trades:
                return

            # Get already-analyzed symbols+timestamps
            analyzed = set()
            try:
                docs = await asyncio.to_thread(
                    lambda: list(
                        firebase_service.db.collection("trade_analytics")
                        .order_by("analyzed_at")
                        .limit(50)
                        .stream()
                    )
                )
                for doc in docs:
                    d = doc.to_dict()
                    key = f"{d.get('symbol', '')}_{d.get('timestamp', '')}"
                    analyzed.add(key)
            except Exception:
                pass

            # Analyze any trades not yet in analytics
            count = 0
            for trade in trades:
                key = f"{trade.get('symbol', '')}_{trade.get('timestamp', '')}"
                if key not in analyzed and trade.get("symbol"):
                    await self.analyze_closed_trade(trade)
                    count += 1
                    await asyncio.sleep(0.5)  # Throttle

            if count > 0:
                logger.info(f"📊 [BATCH] Analyzed {count} previously untracked trades")

        except Exception as e:
            logger.error(f"Batch analysis error: {e}")


# Global Instance
trade_analyst = TradeAnalyst()
