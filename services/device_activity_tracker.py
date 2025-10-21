from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DeviceActivityTracker:
    """
    Śledzi ostatnią aktywność urządzeń w sieci.
    Urządzenie jest uznawane za 'online' jeśli przesłało dane w ciągu ostatnich 2 minut.
    """

    _instance = None
    _last_activity: Dict[str, datetime] = {}
    _timeout_minutes = 2  # Timeout w minutach

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DeviceActivityTracker, cls).__new__(cls)
            cls._last_activity = {}
        return cls._instance

    @classmethod
    def update_activity(cls, device_id: str):
        """
        Aktualizuje timestamp ostatniej aktywności dla urządzenia.

        Args:
            device_id: ID urządzenia
        """
        device_id_clean = str(device_id).strip()
        cls._last_activity[device_id_clean] = datetime.now()
        logger.debug(f"Zaktualizowano aktywność dla urządzenia: {device_id_clean}")

    @classmethod
    def is_device_online(cls, device_id: str) -> bool:
        """
        Sprawdza czy urządzenie jest online (przesłało dane w ciągu ostatnich 2 minut).

        Args:
            device_id: ID urządzenia

        Returns:
            True jeśli urządzenie jest online, False w przeciwnym razie
        """
        device_id_clean = str(device_id).strip()

        if device_id_clean not in cls._last_activity:
            return False

        last_seen = cls._last_activity[device_id_clean]
        timeout = timedelta(minutes=cls._timeout_minutes)

        is_online = (datetime.now() - last_seen) < timeout

        return is_online

    @classmethod
    def get_last_seen(cls, device_id: str) -> Optional[datetime]:
        """
        Zwraca timestamp ostatniej aktywności urządzenia.

        Args:
            device_id: ID urządzenia

        Returns:
            Datetime ostatniej aktywności lub None jeśli urządzenie nie było widziane
        """
        device_id_clean = str(device_id).strip()
        return cls._last_activity.get(device_id_clean)

    @classmethod
    def get_all_devices_status(cls) -> Dict[str, dict]:
        """
        Zwraca status wszystkich znanych urządzeń.

        Returns:
            Słownik z device_id jako kluczem i dict ze statusem jako wartością
        """
        result = {}

        for device_id, last_seen in cls._last_activity.items():
            is_online = cls.is_device_online(device_id)
            time_since_last_seen = datetime.now() - last_seen

            result[device_id] = {
                'online': is_online,
                'last_seen': last_seen.isoformat(),
                'seconds_since_last_seen': int(time_since_last_seen.total_seconds())
            }

        return result

    @classmethod
    def set_timeout(cls, minutes: int):
        """
        Ustawia timeout dla określania statusu online/offline.

        Args:
            minutes: Liczba minut
        """
        cls._timeout_minutes = minutes
        logger.info(f"Timeout aktywności urządzeń ustawiony na: {minutes} minut")


# Singleton instance
device_activity_tracker = DeviceActivityTracker()