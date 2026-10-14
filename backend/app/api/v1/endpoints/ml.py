# -*- coding: utf-8 -*-
"""
1CRYPTEN 7.0 — Fine-Tuning & Model Calibration Endpoints
Exposes controls to generate training datasets, recalibrate decision priors,
and inspect model fine-tuning status for Laya and Kronos.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Dict, Any, Optional

from app.ml.fine_tuning.dataset_generator import dataset_generator
from app.ml.fine_tuning.laya_finetune_trainer import laya_trainer
from app.ml.fine_tuning.kronos_adapter_trainer import kronos_trainer

router = APIRouter()


@router.post("/generate-dataset")
async def generate_dataset(min_laya_samples: int = Query(50, ge=10, le=500), kronos_sequences: int = Query(60, ge=10, le=500)):
    """Gera datasets de fine-tuning formatados em JSONL para Laya e Kronos."""
    try:
        laya_res = await dataset_generator.generate_laya_dataset(min_samples=min_laya_samples)
        kronos_res = await dataset_generator.generate_kronos_dataset(num_sequences=kronos_sequences)
        return {
            "status": "success",
            "message": "Datasets gerados com sucesso.",
            "laya_dataset": laya_res,
            "kronos_dataset": kronos_res
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dataset-stats")
async def get_dataset_stats():
    """Retorna estatísticas dos datasets de fine-tuning presentes no disco."""
    return dataset_generator.get_dataset_stats()


@router.post("/train-laya")
async def train_laya_calibration():
    """Dispara o pipeline de calibração/fine-tuning do modelo Laya."""
    try:
        result = await laya_trainer.run_training_pipeline()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train-kronos")
async def train_kronos_adapter():
    """Dispara a calibração do adaptador do modelo autoregressivo Kronos."""
    try:
        result = await kronos_trainer.train_adapter()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_models_status():
    """Retorna status de calibração e fine-tuning de Laya e Kronos."""
    from services.kronos_scorer import kronos_scorer
    from app.services.laya_router_service import laya_sovereign_engine

    return {
        "conductor": "LAYA SOBERANA",
        "laya": {
            "is_calibrated": laya_trainer.get_calibration_status()["is_calibrated"],
            "calibration_info": laya_trainer.get_calibration_status(),
            "model_type": "convaiinnovations/laya-multilingual",
            "regime_mode": getattr(laya_sovereign_engine, "regime_mode", "MEAN_REVERSION")
        },
        "kronos": {
            "is_calibrated": kronos_trainer.get_adapter_status()["is_calibrated"],
            "adapter_info": kronos_trainer.get_adapter_status(),
            "model_name": getattr(kronos_scorer, "model_name", "NeoQuasar/Kronos-mini"),
            "mode": "REAL" if getattr(kronos_scorer, "is_real", False) else "MOCK"
        }
    }
