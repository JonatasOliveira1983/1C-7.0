# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from services.auth_service import get_current_user, User
from services.firebase_service import firebase_service
import asyncio
import time
from typing import List, Dict, Any, Optional

router = APIRouter(prefix="/api/messages", tags=["Messages"])

@router.get("/", response_model=List[Dict[str, Any]])
async def get_messages(current_user: User = Depends(get_current_user)):
    """Busca notificações e anúncios para o usuário logado"""
    if not firebase_service.is_active:
        return []
        
    try:
        def _get():
            # Busca anúncios globais
            global_announcements = firebase_service.db.collection("announcements").order_by("timestamp", direction="DESCENDING").limit(5).stream()
            
            # Busca mensagens diretas para o usuário
            direct_messages = firebase_service.db.collection("users").document(current_user.username)\
                .collection("notifications").order_by("timestamp", direction="DESCENDING").limit(10).stream()
            
            results = []
            for doc in global_announcements:
                d = doc.to_dict()
                d["id"] = doc.id
                d["type"] = "announcement"
                results.append(d)
                
            for doc in direct_messages:
                d = doc.to_dict()
                d["id"] = doc.id
                d["type"] = "direct"
                results.append(d)
            
            # Ordena por timestamp final
            results.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
            return results
            
        return await asyncio.to_thread(_get)
    except Exception as e:
        return []

@router.post("/broadcast")
async def send_broadcast(message: Dict[str, str], current_user: User = Depends(get_current_user)):
    """Envia um anúncio global (Apenas Admin)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Apenas administradores podem enviar broadcast.")
        
    title = message.get("title", "Comunicado Oficial")
    text = message.get("text", "")
    
    try:
        data = {
            "title": title,
            "text": text,
            "timestamp": time.time(),
            "author": current_user.username
        }
        await asyncio.to_thread(firebase_service.db.collection("announcements").add, data)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
