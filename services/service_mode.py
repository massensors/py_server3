class ServiceMode:
    """
    Singleton class do zarządzania trybem serwisowym
    """
    _instance = None
    _service_mode_enabled = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceMode, cls).__new__(cls)
        return cls._instance

    @classmethod
    def is_enabled(cls) -> bool:
        """Sprawdza czy tryb serwisowy jest włączony"""
        instance = cls()
        return instance._service_mode_enabled

    @classmethod
    def set_enabled(cls, enabled: bool) -> None:
        """Ustawia stan trybu serwisowego"""
        instance = cls()
        instance._service_mode_enabled = enabled

    @classmethod
    def get_request_value(cls) -> int:
        """Zwraca wartość request na podstawie stanu trybu serwisowego"""
        return 3 if cls.is_enabled() else 0