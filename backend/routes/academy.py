# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from services.auth_service import get_current_user, User
from services.firebase_service import firebase_service
import asyncio
import time
from typing import List, Dict, Any

router = APIRouter(prefix="/api/academy", tags=["Academy"])

@router.get("/lessons", response_model=List[Dict[str, Any]])
async def get_lessons(current_user: User = Depends(get_current_user)):
    """Busca a lista de aulas e o progresso do usuário"""
    if not firebase_service.is_active:
        await firebase_service.initialize()
        
    try:
        # 1. Busca metadados das aulas
        def _get_lessons():
            docs = firebase_service.db.collection("academy_lessons").order_by("order").stream()
            return [ {**doc.to_dict(), "id": doc.id} for doc in docs ]
            
        lessons = await asyncio.to_thread(_get_lessons)
        
        # 2. Busca progresso do usuário
        user_doc = await asyncio.to_thread(
            firebase_service.db.collection("users").document(current_user.username).get
        )
        progress = []
        if user_doc.exists:
            progress = user_doc.to_dict().get("academy_progress", [])
            
        # Marca aulas completas
        for lesson in lessons:
            lesson["completed"] = lesson["id"] in progress
            
        return lessons
    except Exception as e:
        # Fallback se a coleção não existir ainda
        return [
            {
                "id": "1",
                "module": "Módulo 1: A Gênese",
                "title": "A Filosofia do Sniper 10D",
                "duration": "12:45",
                "youtubeId": "dQw4w9WgXcQ",
                "description": "Entenda a mentalidade necessária para operar o sistema soberano.",
                "order": 1,
                "completed": False
            }
        ]

@router.post("/lessons/{lesson_id}/complete")
async def complete_lesson(lesson_id: str, current_user: User = Depends(get_current_user)):
    """Marca uma aula como concluída para o usuário"""
    try:
        user_ref = firebase_service.db.collection("users").document(current_user.username)
        
        def _update():
            doc = user_ref.get()
            if doc.exists:
                progress = doc.to_dict().get("academy_progress", [])
                if lesson_id not in progress:
                    progress.append(lesson_id)
                    user_ref.update({"academy_progress": progress})
            return True
            
        await asyncio.to_thread(_update)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
