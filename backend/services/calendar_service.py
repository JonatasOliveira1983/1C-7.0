import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from services.firebase_service import firebase_service

logger = logging.getLogger("CalendarService")

class CalendarService:
    """
    [V20.5] JARVIS Calendar & Schedule Service.
    Manages reminders and appointments locally with ready-to-sync architecture.
    """
    
    def __init__(self):
        self.db_collection = "admiral_agenda"
        
    async def add_event(self, title: str, description: str, scheduled_at: float, category: str = "COMPROMISSO"):
        """Adiciona um evento à agenda do Almirante."""
        event = {
            "title": title,
            "description": description,
            "scheduled_at": scheduled_at, # Timestamp
            "category": category.upper(),
            "created_at": time.time(),
            "status": "PENDING"
        }
        try:
            # Firestore persist
            await firebase_service.db.collection(self.db_collection).add(event)
            logger.info(f"📅 [AGENDA] Evento adicionado: {title} p/ {datetime.fromtimestamp(scheduled_at)}")
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar evento na agenda: {e}")
            return False

    async def get_upcoming_events(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Recupera os próximos compromissos."""
        try:
            now = time.time()
            query = firebase_service.db.collection(self.db_collection)\
                .where("scheduled_at", ">=", now)\
                .where("status", "==", "PENDING")\
                .order_by("scheduled_at")\
                .limit(limit)
            
            docs = await query.get()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Erro ao buscar agenda: {e}")
            return []

    async def check_reminders(self) -> List[Dict[str, Any]]:
        """Verifica se há eventos precisando de lembrete agora (janela de 5 min)."""
        now = time.time()
        upcoming = await self.get_upcoming_events(limit=10)
        reminders = []
        for event in upcoming:
            # Se faltar menos de 10 minutos
            diff = event['scheduled_at'] - now
            if 0 < diff <= 600: # 10 minutos
                reminders.append(event)
        return reminders

calendar_service = CalendarService()
