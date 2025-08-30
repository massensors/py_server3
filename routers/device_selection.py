import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional

from repositories.database import get_db
from models.models import Aliases, StaticParams, MeasureData
from services.selected_device_store import selected_device_store

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/device-selection",
    tags=["device selection"],
    responses={404: {"description": "Not found"}}
)

class DeviceSelectionRequest(BaseModel):
    device_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "98369337"
            }
        }

class DeviceSelectionResponse(BaseModel):
    status: str
    message: str
    selected_device_id: Optional[str] = None
    device_exists: bool = False
    device_info: Optional[Dict[str, Any]] = None

@router.post("/select", response_model=DeviceSelectionResponse)
async def select_device(request: DeviceSelectionRequest, db: Session = Depends(get_db)):
    """
    Wybierz urządzenie do pracy - zapisz w rejestrze i sprawdź czy istnieje w bazie
    """
    device_id = request.device_id.strip()

    if not device_id:
        raise HTTPException(status_code=400, detail="Device ID nie może być pusty")

    # Zapisz w rejestrze
    selected_device_store.set_device_id(device_id)

    # Sprawdź czy urządzenie istnieje w bazie danych
    device_info = {}
    device_exists = False

    try:
        # Sprawdź w tabelach - aliasy
        alias = db.query(Aliases).filter(Aliases.deviceId == device_id).first()
        if alias:
            device_info["alias"] = {
                "company": alias.company,
                "location": alias.location,
                "productName": alias.productName,
                "scaleId": alias.scaleId
            }
            device_exists = True

        # Sprawdź parametry statyczne
        static_params = db.query(StaticParams).filter(StaticParams.deviceId == device_id).first()
        if static_params:
            device_info["static_params"] = {
                "filterRate": static_params.filterRate,
                "scaleCapacity": static_params.scaleCapacity,
                "scaleType": static_params.scaleType,
                "loadcellCapacity": static_params.loadcellCapacity
            }
            device_exists = True

        # Sprawdź dane pomiarowe (tylko najnowsze)
        latest_measure = (
            db.query(MeasureData)
            .filter(MeasureData.deviceId == device_id)
            .order_by(MeasureData.id.desc())
            .first()
        )
        if latest_measure:
            device_info["latest_measure"] = {
                "speed": latest_measure.speed,
                "rate": latest_measure.rate,
                "total": latest_measure.total,
                "currentTime": latest_measure.currentTime
            }
            device_exists = True

        # Policz wszystkie pomiary
        measures_count = db.query(MeasureData).filter(MeasureData.deviceId == device_id).count()
        if measures_count > 0:
            device_info["measures_count"] = measures_count

    except Exception as e:
        logger.error(f"Błąd podczas sprawdzania urządzenia {device_id}: {e}")

    return DeviceSelectionResponse(
        status="success",
        message=f"Wybrano urządzenie: {device_id}",
        selected_device_id=device_id,
        device_exists=device_exists,
        device_info=device_info if device_info else None
    )

@router.get("/current", response_model=DeviceSelectionResponse)
async def get_current_selection(db: Session = Depends(get_db)):
    """
    Pobierz informacje o aktualnie wybranym urządzeniu
    """
    device_id = selected_device_store.get_device_id()

    if not device_id:
        return DeviceSelectionResponse(
            status="success",
            message="Brak wybranego urządzenia",
            selected_device_id=None,
            device_exists=False
        )

    # Sprawdź czy urządzenie nadal istnieje w bazie
    device_exists = (
            db.query(Aliases).filter(Aliases.deviceId == device_id).first() is not None or
            db.query(StaticParams).filter(StaticParams.deviceId == device_id).first() is not None or
            db.query(MeasureData).filter(MeasureData.deviceId == device_id).first() is not None
    )

    return DeviceSelectionResponse(
        status="success",
        message=f"Aktualnie wybrane urządzenie: {device_id}",
        selected_device_id=device_id,
        device_exists=device_exists
    )

@router.delete("/clear")
async def clear_selection():
    """
    Wyczyść wybór urządzenia
    """
    old_device_id = selected_device_store.get_device_id()
    selected_device_store.clear_selection()

    return {
        "status": "success",
        "message": f"Usunięto wybór urządzenia: {old_device_id}",
        "previous_device_id": old_device_id
    }

@router.get("/info")
async def get_selection_info():
    """
    Pobierz podstawowe informacje o stanie wyboru
    """
    device_id = selected_device_store.get_device_id()
    return {
        "has_selection": selected_device_store.has_selected_device(),
        "selected_device_id": device_id,
        "is_selected": lambda check_id: selected_device_store.is_device_selected(check_id) if device_id else False
    }