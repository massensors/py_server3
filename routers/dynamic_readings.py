
from fastapi import APIRouter
from pydantic import BaseModel
from services.dynamic_mode import dynamic_readings_store
from services.dynamic_mode import dynamic_mode_response
from services.service_mode import ServiceMode
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dynamic-readings",
    tags=["dynamic-readings"],
    responses={404: {"description": "Not found"}}
)


class DynamicReadingsResponse(BaseModel):
    device_id: str = ""
    mv_reading: str = ""
    conv_digits: str = ""
    scale_weight: str = ""
    belt_weight: str = ""
    current_time: str = ""
    has_data: bool = False


@router.get("/readings", response_model=DynamicReadingsResponse)
async def get_dynamic_readings():
    """
    Pobiera aktualne odczyty dynamiczne
    """
    readings = dynamic_readings_store.get_readings()
    has_data = dynamic_readings_store.has_readings()

    if has_data:
        return DynamicReadingsResponse(
            device_id=readings.get('device_id', ''),
            mv_reading=readings.get('mv_reading', ''),
            conv_digits=readings.get('conv_digits', ''),
            scale_weight=readings.get('scale_weight', ''),
            belt_weight=readings.get('belt_weight', ''),
            current_time=readings.get('current_time', ''),
            has_data=True
        )
    else:
        return DynamicReadingsResponse(has_data=False)


@router.post("/activate")
async def activate_readings_mode():
    """
    Aktywuje tryb odczytów (ustawia request_value = 0x02 w ServiceMode)
    """
    # Aktywacja trybu odczytów w ServiceMode
    ServiceMode.activate_readings_mode()

    # Również aktywacja w DynamicModeResponse jeśli istnieje
    try:
        dynamic_mode_response.activate_reading_mode()
    except Exception as e:
        logger.warning(f"Błąd aktywacji w dynamic_mode_response: {e}")

    logger.info("Aktywowano tryb odczytów dynamicznych")

    return {
        "message": "Tryb odczytów aktywowany",
        "request_value": ServiceMode.get_request_value(),
        "request_mode": ServiceMode.get_request_mode()
    }


@router.post("/deactivate")
async def deactivate_readings_mode():
    """
    Deaktywuje tryb odczytów
    """
    # Deaktywacja trybu odczytów w ServiceMode
    ServiceMode.deactivate_readings_mode()

    # Również deaktywacja w DynamicModeResponse jeśli istnieje
    try:
        dynamic_mode_response.deactivate_reading_mode()
    except Exception as e:
        logger.warning(f"Błąd deaktywacji w dynamic_mode_response: {e}")

    logger.info("Deaktywowano tryb odczytów dynamicznych")

    return {
        "message": "Tryb odczytów deaktywowany",
        "request_value": ServiceMode.get_request_value(),
        "request_mode": ServiceMode.get_request_mode()
    }