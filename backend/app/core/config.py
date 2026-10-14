import os
from pathlib import Path
from typing import Optional, List, Set
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / ".env.local")
load_dotenv(BASE_DIR / ".env.production")

class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "1Crypten 7.0 — Elite Trading System")
    VERSION: str = "V136-SWING"
    DEPLOYMENT_ID: str = "V136_SWING_PATTERNS"
    API_V1_STR: str = "/api/v1"
    PORT: int = int(os.getenv("PORT", 8085))

    # Base e Diretórios
    BASE_DIR: Path = BASE_DIR
    STORAGE_DIR: Path = BASE_DIR / "storage"
    DATA_DIR: Path = BASE_DIR / "data"
    STATIC_DIR: Path = Path(__file__).resolve().parent.parent / "static"

    # Banco de Dados: PostgreSQL (SSOT) ou SQLite local automático
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR}/local_sniper.db"
    )

    # Autenticação e Segurança
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "1crypten-railway-secret-2026-prod")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 dias
    ENCRYPTION_PASSWORD: str = os.getenv("ENCRYPTION_PASSWORD", "1crypten-encryption-password-2026")
    ENCRYPTION_SALT: str = os.getenv("ENCRYPTION_SALT", "1crypten-encryption-salt-2026")

    # OKX Exchange Configs
    OKX_EXECUTION_MODE: str = os.getenv("OKX_EXECUTION_MODE", "PAPER").upper()
    OKX_API_KEY_MASTER: str = os.getenv("OKX_API_KEY_MASTER", "")
    OKX_API_SECRET_MASTER: str = os.getenv("OKX_API_SECRET_MASTER", "")
    OKX_PASSPHRASE_MASTER: str = os.getenv("OKX_PASSPHRASE_MASTER", "")
    OKX_TESTNET: bool = os.getenv("OKX_TESTNET", "False").lower() in ("true", "1", "yes")
    OKX_SIMULATED_BALANCE: float = float(os.getenv("OKX_SIMULATED_BALANCE", 100.0))

    # Alavancagem e Slots de Risco
    LEVERAGE: int = 50
    LEVERAGE_RANGING: int = 50
    LEVERAGE_TRENDING: int = 50
    MAX_SLOTS: int = 20
    MAX_SLOTS_LATERAL: int = 16
    MAX_SLOTS_TRENDING: int = 16
    MARGIN_PER_TRADE_LATERAL: float = 0.50
    MARGIN_PER_TRADE_TRENDING: float = 0.50
    RISK_CAP_PERCENT: float = 0.40  # 40% da banca alocada no total
    MAX_INITIAL_STOP_ROI: float = 30.0

    # Risco Zero e Breakeven
    RISK_ZERO_TRIGGER_ROI: float = 50.0
    RISK_ZERO_STOP_TARGET: float = 25.0
    BREAKEVEN_TRIGGER_PERCENT: float = 5.0
    WIN_ROI_THRESHOLD: float = 80.0

    # Regime de Mercado (ADX)
    ADX_MIN_ENTRY: float = 22.0
    ADX_TRENDING_THRESHOLD: float = 25.0
    ADX_STRONG_TREND_THRESHOLD: float = 30.0

    # Decor Hunter
    DECOR_HUNTER_MAX_SLOTS: int = 8
    DECOR_HUNTER_MIN_CONFIDENCE: float = 70.0
    DECOR_HUNTER_SCAN_INTERVAL: int = 30

    # Swing Lab (2H S/R)
    SWING_LEVERAGE: int = 50
    SWING_MARGIN_PER_TRADE: float = 200.0
    SWING_SCAN_INTERVAL: int = 1800  # 30min
    SWING_STOP_ROI: float = 20.0
    SWING_TP_ENABLED: bool = True
    SWING_TP_MIN_DISTANCE: float = 5.0
    SWING_TP_MAX_DISTANCE: float = 100.0

    # Equity Defense
    EQUITY_DEFENSE_LOCK_RATIO: float = 0.80
    EQUITY_DEFENSE_STOP_L1: float = 7.0
    EQUITY_DEFENSE_STOP_L2: float = 5.0
    EQUITY_DEFENSE_STOP_L3: float = 3.0
    EQUITY_DEFENSE_MIN_ROI: float = 5.0

    # Kronos Conviction Scorer
    KRONOS_ENABLED: bool = os.getenv("KRONOS_ENABLED", "true").lower() in ("true", "1", "yes")
    KRONOS_MODEL_NAME: str = os.getenv("KRONOS_MODEL_NAME", "kronos-mini")
    KRONOS_SCORE_WEIGHT: float = float(os.getenv("KRONOS_SCORE_WEIGHT", 0.18))
    KRONOS_INTERVAL: str = os.getenv("KRONOS_INTERVAL", "5")
    KRONOS_CACHE_TTL: int = int(os.getenv("KRONOS_CACHE_TTL", 60))
    KRONOS_TIMEOUT: float = float(os.getenv("KRONOS_TIMEOUT", 5.0))
    KRONOS_FALLBACK_SCORE: float = float(os.getenv("KRONOS_FALLBACK_SCORE", 50.0))

    # IA Híbrida: Hermes, Laya, DeepSeek Cloud
    LLM_ENGINE: str = os.getenv("LLM_ENGINE", "deepseek").lower()
    ENABLE_LOCAL_LLM_WARMUP: bool = os.getenv("ENABLE_LOCAL_LLM_WARMUP", "false").lower() in ("true", "1", "yes")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

settings = Settings()
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
