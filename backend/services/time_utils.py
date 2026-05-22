# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, timezone

def get_br_time() -> datetime:
    """Retorna a data e hora atual no fuso horário de Brasília (UTC-3)."""
    return datetime.now(timezone(timedelta(hours=-3)))

def get_br_time_str() -> str:
    """Retorna a data e hora atual formatada para logs (DD/MM/YYYY, HH:MM:SS)."""
    return get_br_time().strftime("%d/%m/%Y, %H:%M:%S")

def get_br_iso_str() -> str:
    """Retorna a data e hora atual no formato ISO (YYYY-MM-DDTHH:MM:SS)."""
    return get_br_time().strftime("%Y-%m-%dT%H:%M:%S")
