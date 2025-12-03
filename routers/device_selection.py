import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional

from repositories.database import get_db
from models.models import Aliases, StaticParams, MeasureData
from services.selected_device_store import selected_device_store
from services.service_mode_manager import service_mode_manager

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
    service_mode_changes: Optional[list] = None


@router.post("/select", response_model=DeviceSelectionResponse)
async def select_device(request: DeviceSelectionRequest, db: Session = Depends(get_db)):
    """
    Wybierz urządzenie do pracy - zapisz w rejestrze i sprawdź czy istnieje w bazie
    """
    device_id = request.device_id.strip()

    if not device_id:
        raise HTTPException(status_code=400, detail="Device ID nie może być pusty")

    # Pobierz aktualne urządzenie przed zmianą
    old_device_id = selected_device_store.get_device_id()

    # Obsługuj zmianę urządzenia z zarządzaniem trybem serwisowym
    if old_device_id != device_id:
        service_changes = service_mode_manager.handle_device_selection_change(device_id, old_device_id)
        logger.info(f"Zmiana urządzenia z '{old_device_id}' na '{device_id}': {service_changes}")
    else:
        service_changes = {"actions_performed": [], "service_mode_changes": []}

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
        device_info=device_info if device_info else None,
        service_mode_changes=service_changes["service_mode_changes"]
    )

# POPRAWIONE - Endpoint do zarządzania trybem serwisowym z lepszym logowaniem
@router.post("/service-mode/enable")
async def enable_service_mode():
    """Włącz tryb serwisowy dla wybranego urządzenia"""
    try:
        logger.debug("Próba włączenia trybu serwisowego...")

        # Sprawdź czy urządzenie jest wybrane
        current_device = selected_device_store.get_device_id()
        logger.debug(f"Aktualne wybrane urządzenie: {current_device}")

        if not current_device:
            logger.warning("Brak wybranego urządzenia podczas próby włączenia trybu serwisowego")
            raise HTTPException(
                status_code=400,
                detail="Brak wybranego urządzenia. Najpierw wybierz urządzenie."
            )

        result = service_mode_manager.enable_service_mode_for_current_device()
        logger.debug(f"Wynik włączenia trybu serwisowego: {result}")

        if result["status"] == "error":
            logger.error(f"Błąd włączenia trybu serwisowego: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])

        logger.info(f"Pomyślnie włączono tryb serwisowy dla urządzenia: {current_device}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Nieoczekiwany błąd podczas włączania trybu serwisowego: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd wewnętrzny: {str(e)}")

@router.get("/service-mode/status")
async def get_service_mode_status():
    """Pobierz status trybu serwisowego"""
    try:
        logger.debug("Pobieranie statusu trybu serwisowego...")
        status = service_mode_manager.get_service_mode_status()
        logger.debug(f"Status trybu serwisowego: {status}")
        return status
    except Exception as e:
        logger.error(f"Błąd podczas pobierania statusu trybu serwisowego: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd pobierania statusu: {str(e)}")

@router.post("/service-mode/disable")
async def disable_service_mode():
    """Wyłącz tryb serwisowy dla wybranego urządzenia"""
    try:
        logger.debug("Próba wyłączenia trybu serwisowego...")

        # Sprawdź czy urządzenie jest wybrane
        current_device = selected_device_store.get_device_id()
        logger.debug(f"Aktualne wybrane urządzenie: {current_device}")

        if not current_device:
            logger.warning("Brak wybranego urządzenia podczas próby wyłączenia trybu serwisowego")
            raise HTTPException(
                status_code=400,
                detail="Brak wybranego urządzenia. Najpierw wybierz urządzenie."
            )

        result = service_mode_manager.disable_service_mode_for_current_device()
        logger.debug(f"Wynik wyłączenia trybu serwisowego: {result}")

        if result["status"] == "error":
            logger.error(f"Błąd wyłączenia trybu serwisowego: {result['message']}")
            raise HTTPException(status_code=400, detail=result["message"])

        logger.info(f"Pomyślnie wyłączono tryb serwisowy dla urządzenia: {current_device}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Nieoczekiwany błąd podczas wyłączania trybu serwisowego: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd wewnętrzny: {str(e)}")

@router.get("/current", response_model=DeviceSelectionResponse)
async def get_current_selection(db: Session = Depends(get_db)):
    """
    Pobierz informacje o aktualnie wybranym urządzeniu
    """
    device_id = selected_device_store.get_device_id()

    # Jeśli brak wyboru, spróbuj znaleźć pierwsze urządzenie w bazie
    if not device_id:
        # Sprawdzamy kolejno tabele, sortując po ID, aby wynik był deterministyczny
        first_entry = (
                db.query(Aliases).order_by(Aliases.deviceId).first() or
                db.query(StaticParams).order_by(StaticParams.deviceId).first() or
                db.query(MeasureData).order_by(MeasureData.deviceId).first()
        )

        if first_entry:
            device_id = first_entry.deviceId
            selected_device_store.set_device_id(device_id)
            logger.info(f"Automatycznie wybrano pierwsze dostępne urządzenie z bazy: {device_id}")

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