# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, status
from services.auth_service import get_current_user, User
from services.firebase_service import firebase_service
import asyncio
import time
from typing import List, Dict, Any

router = APIRouter(prefix="/api/admin", tags=["Admin"])

async def check_admin_role(current_user: User = Depends(get_current_user)):
    """Middleware para garantir que apenas admins acessem estas rotas"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Requer privilégios de administrador."
        )
    return current_user

@router.get("/users", response_model=List[Dict[str, Any]])
async def get_all_users(admin: User = Depends(check_admin_role)):
    """Lista todos os usuários registrados no sistema"""
    if not firebase_service.is_active:
        await firebase_service.initialize()
        
    try:
        def _get():
            docs = firebase_service.db.collection("users").stream()
            users = []
            for doc in docs:
                u = doc.to_dict()
                # Removemos campos sensíveis
                if "hashed_password" in u:
                    del u["hashed_password"]
                # Adicionamos o ID do documento (handle) se não estiver no dict
                u["username"] = doc.id
                users.append(u)
            return users
            
        users = await asyncio.to_thread(_get)
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar usuários: {str(e)}")

@router.get("/stats")
async def get_system_stats(admin: User = Depends(check_admin_role)):
    """Retorna estatísticas globais do ecossistema"""
    if not firebase_service.is_active:
        await firebase_service.initialize()
        
    try:
        # Busca banca (exemplo simplificado, poderia ser um agregado no multitenant)
        banca = await firebase_service.get_banca_status()
        
        # Busca total de usuários
        def _count():
            return len(list(firebase_service.db.collection("users").stream()))
            
        total_users = await asyncio.to_thread(_count)
        
        # Busca estado do Lockdown no RTDB (se existir)
        lockdown_active = False
        if firebase_service.rtdb:
            lockdown_val = await asyncio.to_thread(firebase_service.rtdb.child("system").child("lockdown").get)
            lockdown_active = bool(lockdown_val)

        return {
            "total_members": total_users,
            "active_snipers": total_users, # Placeholder: filtrar por subscrição ativa futuramente
            "managed_assets": banca.get("saldo_total", 0),
            "system_health": "99.9%",
            "lockdown_active": lockdown_active,
            "timestamp_sync": time.time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar estatísticas: {str(e)}")

@router.post("/user/{username}/status")
async def update_user_status(username: str, status_data: Dict[str, str], admin: User = Depends(check_admin_role)):
    """Atualiza o status de um usuário (active, suspended, trial)"""
    new_status = status_data.get("status")
    if new_status not in ["active", "suspended", "trial"]:
        raise HTTPException(status_code=400, detail="Status inválido.")
        
    try:
        await asyncio.to_thread(
            firebase_service.db.collection("users").document(username).set,
            {"status": new_status},
            merge=True
        )
        return {"message": f"Status de {username} atualizado para {new_status}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar status: {str(e)}")

@router.post("/lockdown")
async def toggle_lockdown(lockdown_data: Dict[str, bool], admin: User = Depends(check_admin_role)):
    """Ativa ou desativa o modo Lockdown global"""
    active = lockdown_data.get("active", False)
    
    try:
        # Salva no Firestore
        await asyncio.to_thread(
            firebase_service.db.collection("system").document("global_config").set,
            {"lockdown": active},
            merge=True
        )
        
        # Sincroniza com RTDB (para parada imediata dos workers se estiverem ouvindo)
        if firebase_service.rtdb:
            await asyncio.to_thread(firebase_service.rtdb.child("system").child("lockdown").set, active)
            
        return {"status": "success", "lockdown_active": active}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao alternar lockdown: {str(e)}")
