class ServiceMode:
    """
    Singleton class do zarządzania trybem serwisowym
    """
    _instance = None
    _enabled = False
    _active = False
    _status_message = "Nieznany status"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceMode, cls).__new__(cls)
        return cls._instance

    @classmethod
    def is_enabled(cls) -> bool:
        """Sprawdza czy tryb serwisowy jest włączony"""
        return cls._enabled

    @classmethod
    def set_enabled(cls, enabled: bool) -> None:
        """Ustawia stan trybu serwisowego"""
        cls._enabled = enabled

    @classmethod
    def get_request_value(cls) -> int:
        """Zwraca wartość request na podstawie stanu trybu serwisowego"""
        return 0x03 if cls._enabled else 0x00

    @classmethod
    def toggle(cls, enabled: bool):
        """Alias dla set_enabled - dla kompatybilności"""
        cls.set_enabled(enabled)

    @classmethod
    def set_status_message(cls, message: str):
        cls._status_message = message

    @classmethod
    def get_status_message(cls) -> str:
        return cls._status_message

    @classmethod
    def get_status_info(cls) -> dict:
        return {
            "enabled": cls._enabled,
            "status_message": cls._status_message,
            "request_value": cls.get_request_value()
        }

    @classmethod
    def is_active(cls) -> bool:
        """Sprawdza czy tryb serwisowy jest aktywny"""
        return cls._active

    @classmethod
    def set_active(cls, active: bool) -> None:
        """Ustawia stan aktywności trybu serwisowego"""
        cls._active = active
