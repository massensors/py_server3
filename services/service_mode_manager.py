import logging
from typing import Optional
from services.selected_device_store import selected_device_store
from services.service_mode import ServiceMode
from services.service_parameter_store import service_parameter_store

logger = logging.getLogger(__name__)


class ServiceModeManager:
    """
    Menedżer do zarządzania przełączaniem trybu serwisowego między urządzeniami
    """

    @staticmethod
    def handle_device_selection_change(new_device_id: str, old_device_id: Optional[str]) -> dict:
        """
        Obsługuje zmianę wybranego urządzenia i zarządza trybem serwisowym

        Args:
            new_device_id: ID nowo wybranego urządzenia
            old_device_id: ID poprzednio wybranego urządzenia

        Returns:
            dict: Informacje o wykonanych akcjach
        """
        result = {
            "actions_performed": [],
            "old_device_id": old_device_id,
            "new_device_id": new_device_id,
            "service_mode_changes": []
        }

        # Sprawdź czy jest urządzenie w trybie serwisowym
        current_service_device = selected_device_store.get_service_mode_device()

        if current_service_device and current_service_device != new_device_id:
            # Inne urządzenie jest w trybie serwisowym - trzeba je wyłączyć
            logger.info(f"Przygotowanie do wyłączenia trybu serwisowego dla urządzenia: {current_service_device}")

            # Zaplanuj wyłączenie trybu serwisowego dla starego urządzenia
            ServiceModeManager._schedule_service_mode_disable(current_service_device)

            result["actions_performed"].append("scheduled_service_mode_disable")
            result["service_mode_changes"].append({
                "device_id": current_service_device,
                "action": "disable_scheduled",
                "reason": "device_selection_changed"
            })

        # Aktualizuj rejestr wybranego urządzenia
        selected_device_store.set_device_id(new_device_id)
        result["actions_performed"].append("device_selection_updated")

        return result

    @staticmethod
    def _schedule_service_mode_disable(device_id: str) -> None:
        """
        Zaplanuj wyłączenie trybu serwisowego dla urządzenia
        Zapisuje parametr do wyłączenia trybu serwisowego w service_parameter_store
        """
        # Zapisz komendę wyłączenia trybu serwisowego
        # Adres parametru 0 oznacza komendę systemową wyłączenia trybu serwisowego
        service_parameter_store.store_parameters(
            device_id=device_id,
            param_address=0,  # Adres specjalny dla wyłączenia trybu serwisowego
            param_data="DISABLE_SERVICE_MODE"
        )

        logger.info(f"Zaplanowano wyłączenie trybu serwisowego dla urządzenia: {device_id}")

    @staticmethod
    def enable_service_mode_for_current_device() -> dict:
        """
        Włącz tryb serwisowy dla aktualnie wybranego urządzenia
        """
        current_device = selected_device_store.get_device_id()

        if not current_device:
            return {
                "status": "error",
                "message": "Brak wybranego urządzenia"
            }

        # Sprawdź czy inne urządzenie jest w trybie serwisowym
        current_service_device = selected_device_store.get_service_mode_device()

        if current_service_device and current_service_device != current_device:
            # Wyłącz tryb serwisowy dla innego urządzenia
            ServiceModeManager._schedule_service_mode_disable(current_service_device)

        # Włącz tryb serwisowy
        ServiceMode.set_enabled(True)
        selected_device_store.set_service_mode_device(current_device)

        logger.info(f"Włączono tryb serwisowy dla urządzenia: {current_device}")

        return {
            "status": "success",
            "message": f"Włączono tryb serwisowy dla urządzenia: {current_device}",
            "device_id": current_device
        }

    @staticmethod
    def disable_service_mode_for_current_device() -> dict:
        """
        Wyłącz tryb serwisowy dla aktualnie wybranego urządzenia
        """
        current_device = selected_device_store.get_device_id()
        service_device = selected_device_store.get_service_mode_device()

        if not current_device:
            return {
                "status": "error",
                "message": "Brak wybranego urządzenia"
            }

        # Wyłącz tryb serwisowy
        ServiceMode.set_enabled(False)

        if service_device == current_device:
            selected_device_store.clear_service_mode_device()

        logger.info(f"Wyłączono tryb serwisowy dla urządzenia: {current_device}")

        return {
            "status": "success",
            "message": f"Wyłączono tryb serwisowy dla urządzenia: {current_device}",
            "device_id": current_device
        }

    @staticmethod
    def get_service_mode_status() -> dict:
        """
        Pobierz aktualny status trybu serwisowego
        """
        selected_device = selected_device_store.get_device_id()
        service_mode_device = selected_device_store.get_service_mode_device()

        return {
            "selected_device": selected_device,
            "service_mode_device": service_mode_device,
            "service_mode_enabled": ServiceMode.is_enabled(),
            "service_mode_active": ServiceMode.is_active(),
            "has_service_mode_device": selected_device_store.has_service_mode_device()
        }


# Globalna instancja
service_mode_manager = ServiceModeManager()