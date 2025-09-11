from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.machine_state import machine_state_observer, MachineStateEnum

router = APIRouter(prefix="/machine-state", tags=["machine-state"])


class NetworkObservationUpdate(BaseModel):
    request_value: Optional[int] = None
    command_id: Optional[str] = None  # Hex string


@router.get("/status")
async def get_observed_state():
    """Pobierz aktualnie obserwowany stan programu"""
    try:
        return {
            "success": True,
            "data": machine_state_observer.get_observation_info()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/variables")
async def get_state_variables():
    """Pobierz aktualne wartości zmiennych stanu"""
    try:
        return {
            "success": True,
            "data": machine_state_observer.get_state_variables()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/observe-network")
async def observe_network_activity(request: NetworkObservationUpdate):
    """
    Zgłoś obserwację aktywności sieciowej
    (wywołane przez CommandHandler)
    """
    try:
        command_id_int = None
        if request.command_id:
            try:
                command_id_int = int(request.command_id, 16)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Nieprawidłowy format command_id: {request.command_id}")

        machine_state_observer.observe_network_activity(
            request_value=request.request_value,
            command_id=command_id_int
        )

        return {
            "success": True,
            "message": "Obserwacja zarejestrowana",
            "data": machine_state_observer.get_observation_info()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check-state/{state}")
async def check_if_in_state(state: str):
    """Sprawdź czy program jest aktualnie w określonym stanie"""
    try:
        state_upper = state.upper()

        try:
            state_enum = MachineStateEnum(state_upper)
        except ValueError:
            available_states = [s.value for s in MachineStateEnum]
            raise HTTPException(
                status_code=400,
                detail=f"Nieznany stan: {state_upper}. Dostępne: {', '.join(available_states)}"
            )

        is_in_state = machine_state_observer.is_in_observed_state(state_enum)

        return {
            "success": True,
            "data": {
                "state": state_enum.value,
                "is_current": is_in_state,
                "current_state": machine_state_observer.get_current_observed_state().value
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/state-definitions")
async def get_state_definitions():
    """Pobierz definicje wszystkich stanów (kombinacje zmiennych)"""
    try:
        definitions = {}
        for state_type in MachineStateEnum:
            if state_type != MachineStateEnum.UNKNOWN_STATE:
                definitions[state_type.value] = machine_state_observer._state_definitions[state_type]

        return {
            "success": True,
            "data": definitions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network-observations")
async def get_network_observations():
    """Pobierz ostatnie obserwacje z sieci"""
    try:
        info = machine_state_observer.get_observation_info()

        return {
            "success": True,
            "data": info['network_observations']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))