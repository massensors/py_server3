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


@router.get("/status", response_model=ServiceModeResponse)
async def get_service_mode_status():
    """
    Pobiera aktualny stan trybu serwisowego
    """
    enabled = ServiceMode.is_enabled()
    request_value = ServiceMode.get_request_value()

    return ServiceModeResponse(enabled=enabled, request_value=request_value)


@router.post("/toggle", response_model=ServiceModeResponse)
async def toggle_service_mode(request: ServiceModeRequest):
    """
    Przełącza tryb serwisowy
    """
    ServiceMode.set_enabled(request.enabled)

    enabled = ServiceMode.is_enabled()
    request_value = ServiceMode.get_request_value()

    return ServiceModeResponse(enabled=enabled, request_value=request_value)