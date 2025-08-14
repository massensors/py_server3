import logging
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from repositories.database import get_db
from services.app_handler import ApplicationHandler, ServiceParameterRequest, ParameterAddresses
from pydantic import BaseModel
from services.service_parameter_store import service_parameter_store

# Konfiguracja loggera
logger = logging.getLogger(__name__)

# Utworzenie routera
router = APIRouter(
    prefix="/app",
    tags=["application interface"],
    responses={404: {"description": "Not found"}}
)

# Inicjalizacja handlera aplikacji
app_handler = ApplicationHandler()


class DeviceParameterResponse(BaseModel):
    """Model odpowiedzi zawierającej parametry urządzenia"""
    status: str
    device_id: str
    parameters: Dict[str, Dict[str, Any]]


class ParameterResponse(BaseModel):
    """Model odpowiedzi zawierającej jeden parametr"""
    status: str
    device_id: str
    parameter: Dict[str, Any]


class UpdateResponse(BaseModel):
    """Model odpowiedzi po aktualizacji parametru"""
    status: str
    message: str
    value: str = None


@router.get("/devices/{device_id}/parameters", response_model=Dict[str, Any])
async def get_device_parameters(device_id: str, db: Session = Depends(get_db)):
    """
    Pobiera wszystkie parametry dla wskazanego urządzenia
    """
    result = app_handler.get_device_parameters(device_id, db)

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])

    return result


@router.get("/devices/{device_id}/parameters/{param_address}", response_model=Dict[str, Any])
async def get_parameter(
        device_id: str,
        param_address: int,
        db: Session = Depends(get_db)
):
    """
    Pobiera wartość konkretnego parametru dla urządzenia
    """
    result = app_handler.get_parameter(device_id, param_address, db)

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])

    return result


@router.put("/devices/{device_id}/parameters/{param_address}", response_model=Dict[str, Any])
async def update_parameter(
        device_id: str,
        param_address: int,
        param_data: str = Body(..., embed=True),
        db: Session = Depends(get_db)
):
    """
    Aktualizuje wartość parametru dla urządzenia
    """
    result = app_handler.update_parameter(device_id, param_address, param_data, db)

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

        # NOWE: Zapisz parametry w store dla kontrolera
    service_parameter_store.store_parameters(device_id, param_address, param_data)
    logger.info(f"Parametry zapisane w store dla kontrolera: {device_id}, {param_address}, {param_data}")

    return result


@router.post("/service-parameter", response_model=Dict[str, Any])
async def update_service_parameter(
        request: ServiceParameterRequest,
        db: Session = Depends(get_db)
):
    """
    Aktualizuje parametr serwisowy na podstawie pełnego żądania
    """
    result = app_handler.update_parameter(
        request.device_id,
        request.param_address,
        request.param_data,
        db
    )

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.get("/parameter-addresses", response_model=Dict[str, Dict[str, Any]])
async def get_parameter_addresses():
    """
    Zwraca mapowanie adresów parametrów na ich nazwy i formaty
    """
    from services.app_handler import PARAMETER_MAPPING
    return PARAMETER_MAPPING