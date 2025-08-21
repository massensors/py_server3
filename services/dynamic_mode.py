from typing import Optional, Dict, Any
import logging
import threading
from datetime import datetime

logger = logging.getLogger(__name__)


class DynamicReadingsStore:
    """
    Singleton do globalnego przechowywania odczytów dynamicznych
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DynamicReadingsStore, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.readings: Dict[str, Any] = {}
            self.last_update: Optional[datetime] = None
            self._initialized = True

    def update_readings(self, device_id: str, mv_reading: str, conv_digits: str,
                       scale_weight: str, belt_weight: str, current_time: str):
        """Aktualizuje odczyty dynamiczne"""
        with self._lock:
            self.readings = {
                'device_id': device_id,
                'mv_reading': mv_reading,
                'conv_digits': conv_digits,
                'scale_weight': scale_weight,
                'belt_weight': belt_weight,
                'current_time': current_time
            }
            self.last_update = datetime.now()
            logger.info(f"Zaktualizowano odczyty dynamiczne dla urządzenia {device_id}")

    def get_readings(self) -> Dict[str, Any]:
        """Pobiera aktualne odczyty"""
        with self._lock:
            return self.readings.copy()

    def has_readings(self) -> bool:
        """Sprawdza czy są dostępne odczyty"""
        with self._lock:
            return bool(self.readings)

    def clear_readings(self):
        """Czyści odczyty"""
        with self._lock:
            self.readings.clear()
            self.last_update = None

# Globalna instancja
dynamic_readings_store = DynamicReadingsStore()




class DynamicModeResponse:
    """
    Singleton do zarządzania trybem dynamicznym z globalnym dostępem
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DynamicModeResponse, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.request_value: int = 0x03  # Domyślnie nieaktywny
            self._initialized = True

    def set_request_value(self, value: int):
        """Ustawia wartość request_value"""
        with self._lock:
            self.request_value = value
            logger.info(f"DynamicModeResponse: request_value ustawione na {hex(value)}")

    def get_request_value(self) -> int:
        """Pobiera aktualną wartość request_value"""
        with self._lock:
            return self.request_value

    def activate_reading_mode(self):
        """Aktywuje tryb odczytów (0x02)"""
        self.set_request_value(0x02)

    def deactivate_reading_mode(self):
        """Deaktywuje tryb odczytów (0x03)"""
        self.set_request_value(0x03)

# Globalna instancja
dynamic_mode_response = DynamicModeResponse()