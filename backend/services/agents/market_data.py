# -*- coding: utf-8 -*-

"""
Market Data: Mapeamento de Setores e Categorias de Ativos
V1.0: Focado nos ~90 pares monitorados pelo Sniper.
"""

SYMBOL_SECTORS = {
    # --- AI (Inteligência Artificial) ---
    "FETUSDT": "AI", "AGIXUSDT": "AI", "OCEANUSDT": "AI", "RNDRUSDT": "AI",
    "NEARUSDT": "AI", "ROSEUSDT": "AI", "TAOUSDT": "AI", "GRTUSDT": "AI",
    "AIUSDT": "AI", "NFPUSDT": "AI", "WLDUSDT": "AI", "ARKMUSDT": "AI",

    # --- MEMES (Explosivos) ---
    "PEPEUSDT": "MEME", "DOGEUSDT": "MEME", "SHIBUSDT": "MEME", "FLOKIUSDT": "MEME",
    "BONKUSDT": "MEME", "WIFUSDT": "MEME", "MYROUSDT": "MEME", "1000SATSUSDT": "MEME",
    "ORDIUSDT": "MEME", "MEMEUSDT": "MEME", "TURBOUSDT": "MEME", "PEOPLEUSDT": "MEME",

    # --- LAYER 1 / SMART CONTRACTS ---
    "BTCUSDT": "L1", "ETHUSDT": "L1", "SOLUSDT": "L1", "ADAUSDT": "L1",
    "DOTUSDT": "L1", "AVAXUSDT": "L1", "MATICUSDT": "L1", "LINKUSDT": "L1",
    "BNBUSDT": "L1", "ATOMUSDT": "L1", "FTMUSDT": "L1", "OPUSDT": "L1",
    "ARBUSDT": "L1", "APTUSDT": "L1", "SUIUSDT": "L1", "SEIUSDT": "L1",
    "NEARUSDT": "L1", # NEAR cross-over AI/L1, L1 primary

    # --- DEFI (Finanças Descentralizadas) ---
    "UNIUSDT": "DEFI", "MKRUSDT": "DEFI", "AAVEUSDT": "DEFI", "SNXUSDT": "DEFI",
    "LDOUSDT": "DEFI", "JUPUSDT": "DEFI", "RUNEUSDT": "DEFI", "INJUSDT": "DEFI",
    "DYDXUSDT": "DEFI", "CRVUSDT": "DEFI", "1INCHUSDT": "DEFI", "GMXUSDT": "DEFI",

    # --- INFRA / STORAGE / MODULAR ---
    "TIAUSDT": "INFRA", "FILUSDT": "INFRA", "ARUSDT": "INFRA", "GRTUSDT": "INFRA",
    "DYMUSDT": "INFRA", "PYTHUSDT": "INFRA", "ALTUSDT": "INFRA",
    
    # --- GAMEFI / NFT ---
    "IMXUSDT": "GAMEFI", "BEAMUSDT": "GAMEFI", "GALAUSDT": "GAMEFI", "AXSUSDT": "GAMEFI",
    "SANDUSDT": "GAMEFI", "MANAUSDT": "GAMEFI", "RONUSDT": "GAMEFI", "APEUSDT": "GAMEFI",

    # --- DEPIN / OTHERS ---
    "HNTUSDT": "DEPIN", "IOTXUSDT": "DEPIN", "POWRUSDT": "DEPIN",
    "TRXUSDT": "PAYMENTS", "XRPUSDT": "PAYMENTS", "LTCUSDT": "PAYMENTS"
}

DEFAULT_SECTOR = "OTHER"

def get_sector(symbol: str) -> str:
    """Retorna o setor para um símbolo (limpa .P e normaliza)."""
    clean_sym = symbol.replace(".P", "").upper()
    if not clean_sym.endswith("USDT") and not clean_sym.endswith("USDC"):
        clean_sym = f"{clean_sym}USDT"
    
    return SYMBOL_SECTORS.get(clean_sym, DEFAULT_SECTOR)

def get_symbols_by_sector(sector: str) -> list:
    """Retorna todos os símbolos mapeados para um setor."""
    return [sym for sym, sec in SYMBOL_SECTORS.items() if sec == sector]
