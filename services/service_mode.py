class ServiceMode:
    """
    Singleton class do zarządzania trybem serwisowym
    """
    _instance = None
    _enabled = False
    _active = False
    _status_message = "Nieznany status"
    _request_mode = "service"  # Nowe pole: "service", "readings", "normal"
    _conveyor_status = "unknown"  # Nowe pole

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceMode, cls).__new__(cls)
        return cls._instance

    @classmethod
    def set_conveyor_status(cls, status: str):
        """Ustawia status przenośnika: 'stopped', 'running', 'error', 'unknown'"""
        cls._conveyor_status = status
       # logger.info(f"Status przenośnika ustawiony na: {status}")

    @classmethod
    def get_conveyor_status(cls) -> str:
        """Zwraca aktualny status przenośnika"""
        return cls._conveyor_status


    @classmethod
    def is_enabled(cls) -> bool:
        """Sprawdza czy tryb serwisowy jest włączony"""
        return cls._enabled

    @classmethod
    def set_enabled(cls, enabled: bool) -> None:
        """Ustawia stan trybu serwisowego"""
        cls._enabled = enabled
        # Gdy wyłączamy tryb serwisowy, resetujemy tryb na normalny
        if not enabled:
            cls._request_mode = "normal"

    @classmethod
    def get_request_value(cls) -> int:
        """Zwraca wartość request na podstawie stanu trybu serwisowego i typu żądania"""
        if not cls._enabled:
            return 0x00  # Tryb normalny/pomiarowy

        # Gdy tryb serwisowy jest włączony, sprawdzamy typ żądania
        if cls._request_mode == "readings":
            return 0x02  # Tryb odczytów dynamicznych
        elif cls._request_mode == "service":
            return 0x03  # Standardowy tryb serwisowy
        else:
            return 0x00  # Fallback - tryb normalny

    @classmethod
    def set_request_mode(cls, mode: str) -> None:
        """
        Ustawia tryb żądania
        Dozwolone wartości: "normal", "service", "readings"
        """
        valid_modes = ["normal", "service", "readings"]
        if mode in valid_modes:
            cls._request_mode = mode
            # Gdy przełączamy na tryb odczytów, automatycznie włączamy tryb serwisowy
            if mode == "readings":
                cls._enabled = True
        else:
            raise ValueError(f"Nieprawidłowy tryb: {mode}. Dozwolone: {valid_modes}")

    @classmethod
    def get_request_mode(cls) -> str:
        """Zwraca aktualny tryb żądania"""
        return cls._request_mode

    @classmethod
    def activate_readings_mode(cls) -> None:
        """Aktywuje tryb odczytów dynamicznych"""
        if cls._enabled:
            cls.set_request_mode("readings")
            cls._status_message = "Tryb odczytów dynamicznych aktywny"
        else:
            cls.set_request_mode("normal")
            cls._status_message = "Tryb normalny"

    @classmethod
    def deactivate_readings_mode(cls) -> None:
        """Deaktywuje tryb odczytów i wraca do standardowego trybu serwisowego"""
        if cls._enabled:
            cls.set_request_mode("service")
            cls._status_message = "Tryb serwisowy aktywny"
        else:
            cls.set_request_mode("normal")
            cls._status_message = "Tryb normalny"

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
            "request_value": cls.get_request_value(),
            "request_mode": cls._request_mode
        }

    @classmethod
    def is_active(cls) -> bool:
        """Sprawdza czy tryb serwisowy jest aktywny"""
        return cls._active

    @classmethod
    def set_active(cls, active: bool) -> None:
        """Ustawia stan aktywności trybu serwisowego"""
        cls._active = active