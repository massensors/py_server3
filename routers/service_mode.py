

from fastapi import APIRouter, HTTPException

from pydantic import BaseModel
import logging

from services.service_mode import ServiceMode
from services.selected_device_store import selected_device_store
from services.service_parameter_store import service_parameter_store


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/service-mode", tags=["service-mode"])


class ServiceModeRequest(BaseModel):
    enabled: bool


@router.get("/status")
async def get_service_mode_status():
    """Pobierz aktualny status trybu serwisowego"""
    return {
        "enabled": ServiceMode.is_enabled(),
        "active": ServiceMode.is_active(),
        "status_message": ServiceMode.get_status_message(),
        "request_mode": ServiceMode.get_request_mode()
    }


@router.post("/toggle")
async def toggle_service_mode(request: ServiceModeRequest):
    """Przełącz tryb serwisowy"""
    ServiceMode.set_enabled(request.enabled)
    ServiceMode.set_request_mode("service")
    # Deaktywuj tryb odczytów, jeśli wyłączamy tryb serwisowy
    if not request.enabled:
        ServiceMode.set_request_mode("normal")
        ServiceMode.deactivate_readings_mode()
        #ServiceMode.set_active(False)
        #ServiceMode.set_enabled(False)
    return {
        "enabled": ServiceMode.is_enabled(),
        "active": ServiceMode.is_active(),
        "status_message": ServiceMode.get_status_message(),
        "request_mode": ServiceMode.get_request_mode()
    }


@router.post("/toggle-for-device")
async def toggle_service_mode_for_device(request: ServiceModeRequest):
    """Przełącz tryb serwisowy dla konkretnego urządzenia"""
    current_device = selected_device_store.get_device_id()

    # Logowanie wartości dla debugowania
    logger.debug(f"Current device: {current_device}")
    logger.debug(f"Has selected device: {selected_device_store.has_selected_device()}")

    if not current_device:
        # Bardziej przyjazny komunikat z instrukcją dla użytkownika
        raise HTTPException(status_code=400, detail="Najpierw wybierz urządzenie, klikając przycisk 'Wybierz' w zakładce 'Urządzenia'")

    # Sprawdź czy inne urządzenie jest w trybie serwisowym
    service_mode_device = selected_device_store.get_service_mode_device()

    if request.enabled:
        # WŁĄCZANIE trybu serwisowego

        # Jeśli inne urządzenie jest w trybie serwisowym - zaplanuj jego wyłączenie
        if service_mode_device and service_mode_device != current_device:
            logger.info(f"Planowanie wyłączenia trybu serwisowego dla urządzenia: {service_mode_device}")
            # Zapisz komendę wyłączenia dla starego urządzenia
            service_parameter_store.store_parameters(
                device_id=service_mode_device,
                param_address=0,
                param_data="DISABLE_SERVICE_MODE"
            )

        # Włącz tryb serwisowy
        ServiceMode.set_enabled(True)
        selected_device_store.set_service_mode_device(current_device)

        logger.info(f"Włączono tryb serwisowy dla urządzenia: {current_device}")

    else:
        # WYŁĄCZANIE trybu serwisowego
        ServiceMode.set_enabled(False)

        # Deaktywuj tryb odczytów
        ServiceMode.deactivate_readings_mode()

        if service_mode_device == current_device:
            selected_device_store.clear_service_mode_device()

        logger.info(f"Wyłączono tryb serwisowy dla urządzenia: {current_device}")

    return {
        "enabled": ServiceMode.is_enabled(),
        "active": ServiceMode.is_active(),
        "status_message": ServiceMode.get_status_message(),
        "device_id": current_device,
        "request_mode": ServiceMode.get_request_mode()
    }
@router.post("/toggle2")
async def toggle_service_mode2(request: ServiceModeRequest):
    """Przełącz tryb serwisowy"""

    # Pobierz aktualne urządzenie (jeśli jest wybrane)
    current_device = selected_device_store.get_device_id()

    # Ustaw stan trybu serwisowego
    ServiceMode.set_enabled(request.enabled)

    # Jeśli włączamy tryb serwisowy i mamy wybrane urządzenie
    if request.enabled and current_device:
        # Sprawdź czy inne urządzenie było w trybie serwisowym
        service_mode_device = selected_device_store.get_service_mode_device()

        if service_mode_device and service_mode_device != current_device:
            logger.info(f"Przełączanie trybu serwisowego z urządzenia {service_mode_device} na {current_device}")
            # Opcjonalnie: zaplanuj wyłączenie dla starego urządzenia
            service_parameter_store.store_parameters(
                device_id=service_mode_device,
                param_address=0,
                param_data="DISABLE_SERVICE_MODE"
            )

        # Ustaw aktualne urządzenie jako urządzenie w trybie serwisowym
        selected_device_store.set_service_mode_device(current_device)
        logger.info(f"Włączono tryb serwisowy dla urządzenia: {current_device}")

    # Jeśli wyłączamy tryb serwisowy
    elif not request.enabled:
        # Deaktywuj tryb odczytów
        ServiceMode.deactivate_readings_mode()

        # Wyczyść informację o urządzeniu w trybie serwisowym
        if current_device:
            service_mode_device = selected_device_store.get_service_mode_device()
            if service_mode_device == current_device:
                selected_device_store.clear_service_mode_device()
                logger.info(f"Wyłączono tryb serwisowy dla urządzenia: {current_device}")

    return {
        "enabled": ServiceMode.is_enabled(),
        "active": ServiceMode.is_active(),
        "status_message": ServiceMode.get_status_message(),
        "request_mode": ServiceMode.get_request_mode(),
        "device_id": current_device if current_device else None
    }