import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SelectedDeviceStore:
    """
    Singleton store do przechowywania informacji o aktualnie wybranym urządzeniu
    """
    _instance = None
    _selected_device_id: Optional[str] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def set_device_id(self, device_id: str) -> None:
        """Ustaw ID aktualnie wybranego urządzenia"""
        old_device_id = self._selected_device_id
        self._selected_device_id = device_id
        logger.info(f"Wybrane urządzenie zmienione z '{old_device_id}' na '{device_id}'")

    def get_device_id(self) -> Optional[str]:
        """Pobierz ID aktualnie wybranego urządzenia"""
        return self._selected_device_id

    def has_selected_device(self) -> bool:
        """Sprawdź czy jakiekolwiek urządzenie jest wybrane"""
        return self._selected_device_id is not None

    def clear_selection(self) -> None:
        """Wyczyść wybór urządzenia"""
        old_device_id = self._selected_device_id
        self._selected_device_id = None
        logger.info(f"Usunięto wybór urządzenia: '{old_device_id}'")

    def is_device_selected(self, device_id: str) -> bool:
        """Sprawdź czy podane urządzenie jest aktualnie wybrane"""
        return self._selected_device_id == device_id

# Globalna instancja
selected_device_store = SelectedDeviceStore()