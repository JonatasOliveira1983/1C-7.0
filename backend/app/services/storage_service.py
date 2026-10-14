import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile

STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / "storage"
MEDIA_DIR = STORAGE_DIR / "rdo_media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

def save_rdo_photo(order_id: str, file_bytes: bytes, filename: str) -> str:
    """Salva foto do canteiro no storage local e retorna a URL relativa."""
    order_folder = MEDIA_DIR / order_id / "photos"
    order_folder.mkdir(parents=True, exist_ok=True)
    
    ext = Path(filename).suffix.lower() or ".jpg"
    photo_id = f"photo_{uuid.uuid4().hex[:8]}{ext}"
    target_path = order_folder / photo_id
    
    with open(target_path, "wb") as f:
        f.write(file_bytes)
        
    return f"/storage/rdo_media/{order_id}/photos/{photo_id}"

def save_rdo_audio(order_id: str, file_bytes: bytes, filename: str) -> Path:
    """Salva gravação de áudio do canteiro no storage e retorna o Path local."""
    order_folder = MEDIA_DIR / order_id / "audio"
    order_folder.mkdir(parents=True, exist_ok=True)
    
    ext = Path(filename).suffix.lower() or ".webm"
    audio_id = f"voice_{uuid.uuid4().hex[:8]}{ext}"
    target_path = order_folder / audio_id
    
    with open(target_path, "wb") as f:
        f.write(file_bytes)
        
    return target_path
