from typing import Optional
import logging
import threading

logger = logging.getLogger(__name__)


class ServiceParameterStore:
    """
    Singleton do przechowywania ostatnich parametrów serwisowych
    z frontend dla późniejszego wykorzystania przez kontroler
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ServiceParameterStore, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.device_id: Optional[str] = None
            self.param_address: Optional[int] = None
            self.param_data: Optional[str] = None
            self._initialized = True

    def store_parameters(self, device_id: str, param_address: int, param_data: str):
        """Zapisuje parametry z frontend"""
        with self._lock:
            self.device_id = device_id
            self.param_address = param_address
            self.param_data = param_data
            logger.info(f"Zapisano parametry serwisowe: device_id={device_id}, "
                        f"param_address={param_address}, param_data='{param_data}'")

    def get_parameters(self) -> tuple[Optional[str], Optional[int], Optional[str]]:
        """Pobiera ostatnie zapisane parametry"""
        with self._lock:
            return self.device_id, self.param_address, self.param_data

    def has_parameters(self) -> bool:
        """Sprawdza czy są zapisane parametry"""
        with self._lock:
            return (self.device_id is not None and
                    self.param_address is not None and
                    self.param_data is not None)

    def clear_parameters(self):
        """Czyści zapisane parametry po wykorzystaniu"""
        with self._lock:
            self.device_id = None
            self.param_address = None
            self.param_data = None
            logger.debug("Wyczyszczono parametry serwisowe")


# Globalna instancja
service_parameter_store = ServiceParameterStore()