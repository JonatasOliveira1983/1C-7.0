# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from services.auth_service import auth_service, Token, User, get_current_user
from pydantic import BaseModel
from typing import Optional
from config import settings
from services.firebase_service import firebase_service
import logging

logger = logging.getLogger("AuthRoute")

router = APIRouter(prefix="/api/auth", tags=["Auth"])

class UserRegister(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None

@router.post("/register")
async def register(user: UserRegister):
    success = await auth_service.register_user(user.dict())
    if not success:
        raise HTTPException(status_code=400, detail="Erro ao registrar usuário.")
    return {"message": "Usuário registrado com sucesso!", "handle": user.username}

@router.post("/login")
async def login(request: Request):
    # Inicializa variáveis
    username = None
    password = None

    # Detecta se é requisição JSON ou Form-Data
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            password = body.get("password")
            username = body.get("username") or "Sovereign"
        except Exception as e:
            logger.error(f"Erro ao ler JSON de autenticação: {e}")
    else:
        try:
            form = await request.form()
            username = form.get("username")
            password = form.get("password")
        except Exception as e:
            logger.error(f"Erro ao ler Form de autenticação: {e}")

    # Bypass de Desenvolvimento / Offline
    # Se a senha for "123" e estivermos em DEBUG ou com o Firebase inativo
    if password == "123" and (settings.DEBUG or not firebase_service.is_active):
        logger.info("🔑 [SOVEREIGN-BYPASS] Login com senha padrão '123' em modo Debug/Offline aprovado.")
        access_token = auth_service.create_access_token(data={"sub": "Sovereign"})
        return {
            "status": "SUCCESS",
            "token": access_token,
            "access_token": access_token,
            "token_type": "bearer"
        }

    # Se não for bypass, valida os dados normais
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de usuário e senha são obrigatórios."
        )

    user = await auth_service.get_user(username)
    if not user or not auth_service.verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(data={"sub": user.username})
    return {
        "status": "SUCCESS",
        "token": access_token,
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

