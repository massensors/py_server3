from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.service_mode import ServiceMode

router = APIRouter(
    prefix="/service-mode",
    tags=["service-mode"],
    responses={404: {"description": "Not found"}}
)


class ServiceModeRequest(BaseModel):
    enabled: bool


class ServiceModeResponse(BaseModel):
    enabled: bool
    request_value: int
    status_message: str = "Nieznany status"  # Dodane nowe pole


@router.get("/status", response_model=ServiceModeResponse)
async def get_service_mode_status():
    """
    Pobiera aktualny stan trybu serwisowego
    """
    enabled = ServiceMode.is_enabled()
    request_value = ServiceMode.get_request_value()
    status_message = ServiceMode.get_status_message()  # Nowa metoda

    return ServiceModeResponse(
        enabled=enabled,
        request_value=request_value,
        status_message=status_message
    )


@router.post("/toggle", response_model=ServiceModeResponse)
async def toggle_service_mode(request: ServiceModeRequest):
    """
    Przełącza tryb serwisowy
    """
    ServiceMode.set_enabled(request.enabled)  # Zachowujesz istniejącą metodę

    enabled = ServiceMode.is_enabled()
    request_value = ServiceMode.get_request_value()
    status_message = ServiceMode.get_status_message()  # Dodana nowa funkcjonalność

    ServiceMode.deactivate_readings_mode()
    return ServiceModeResponse(
        enabled=enabled,
        request_value=request_value,
        status_message=status_message
    )