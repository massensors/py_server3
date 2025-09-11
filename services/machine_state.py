from enum import Enum
from typing import Dict, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class MachineStateEnum(Enum):
    """Enumeracja stanów programu"""
    SERVICE_MODE = "SERVICE_MODE"
    SERVICE_MODE_REQUEST_DYNAMIC = "SERVICE_MODE_REQUEST_DYNAMIC"
    DYNAMIC_MODE = "DYNAMIC_MODE"
    SERVICE_MODE_REQUEST_NORMAL = "SERVICE_MODE_REQUEST_NORMAL"
    NORMAL_MODE = "NORMAL_MODE"
    NORMAL_MODE_REQUEST_SERVICE = "NORMAL_MODE_REQUEST_SERVICE"
    UNKNOWN_STATE = "UNKNOWN_STATE"


class MachineStateObserver:
    """
    Klasa obserwująca stan programu na podstawie ruchu sieciowego
    NIE KONTROLUJE stanu - tylko go obserwuje i identyfikuje
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MachineStateObserver, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        # Zmienne stanu - TYLKO DO ODCZYTU (odzwierciedlają rzeczywisty stan)
        self.service_mode_request: bool = False
        self.service_mode_active: bool = False
        self.dynamic_mode_request: bool = False
        self.dynamic_mode_active: bool = False
        self.normal_mode_request: bool = False
        self.normal_mode_active: bool = False

        # Ostatnie obserwowane wartości z sieci
        self._last_observed_request_value: Optional[int] = None
        self._last_observed_command_id: Optional[int] = None

        # Callback do powiadamiania o zmianach stanu
        self._state_change_callbacks: list[Callable] = []

        # Tablica stanów - definicja kombinacji zmiennych dla każdego stanu
        self._state_definitions: Dict[MachineStateEnum, Dict[str, bool]] = {
            MachineStateEnum.SERVICE_MODE: {
                'service_mode_request': True,
                'service_mode_active': True,
                'dynamic_mode_request': False,
                'dynamic_mode_active': False,
                'normal_mode_request': False,
                'normal_mode_active': False
            },
            MachineStateEnum.SERVICE_MODE_REQUEST_DYNAMIC: {
                'service_mode_request': False,
                'service_mode_active': True,
                'dynamic_mode_request': True,
                'dynamic_mode_active': False,
                'normal_mode_request': False,
                'normal_mode_active': False
            },
            MachineStateEnum.DYNAMIC_MODE: {
                'service_mode_request': False,
                'service_mode_active': False,
                'dynamic_mode_request': True,
                'dynamic_mode_active': True,
                'normal_mode_request': False,
                'normal_mode_active': False
            },
            MachineStateEnum.SERVICE_MODE_REQUEST_NORMAL: {
                'service_mode_request': False,
                'service_mode_active': True,
                'dynamic_mode_request': False,
                'dynamic_mode_active': False,
                'normal_mode_request': True,
                'normal_mode_active': False
            },
            MachineStateEnum.NORMAL_MODE: {
                'service_mode_request': False,
                'service_mode_active': False,
                'dynamic_mode_request': False,
                'dynamic_mode_active': False,
                'normal_mode_request': True,
                'normal_mode_active': True
            },
            MachineStateEnum.NORMAL_MODE_REQUEST_SERVICE: {
                'service_mode_request': True,
                'service_mode_active': False,
                'dynamic_mode_request': False,
                'dynamic_mode_active': False,
                'normal_mode_request': False,
                'normal_mode_active': True
            }
        }

        self._initialized = True

    def observe_network_activity(self, request_value: Optional[int] = None, command_id: Optional[int] = None):
        """
        Obserwuje aktywność sieciową i aktualizuje zmienne stanu
        Ta metoda TYLKO obserwuje - nie kontroluje stanu programu

        Args:
            request_value: Wartość pola request z twojej odpowiedzi (0, 2, 3)
            command_id: ID komendy klienta (0x0000, 0x0004, 0x0006)
        """
        old_state = self.get_current_observed_state()
        state_changed = False

        # Aktualizuj obserwowane wartości
        if request_value is not None and self._last_observed_request_value != request_value:
            self._last_observed_request_value = request_value
            self._update_request_variables(request_value)
            state_changed = True
            logger.debug(f"Obserwowano zmianę request_value na: {request_value}")

        if command_id is not None and self._last_observed_command_id != command_id:
            self._last_observed_command_id = command_id
            self._update_active_variables(command_id)
            state_changed = True
            logger.debug(f"Obserwowano zmianę command_id na: {hex(command_id)}")

        # Sprawdź czy stan się zmienił
        if state_changed:
            new_state = self.get_current_observed_state()
            if old_state != new_state:
                logger.info(f"Obserwowano zmianę stanu programu: {old_state.value if old_state else 'UNKNOWN'} -> {new_state.value if new_state else 'UNKNOWN'}")
                self._notify_state_change(old_state, new_state)

    def _update_request_variables(self, request_value: int):
        """
        Aktualizuje zmienne *_request na podstawie obserwowanej wartości request
        """
        # Resetuj wszystkie request variables
        self.service_mode_request = False
        self.dynamic_mode_request = False
        self.normal_mode_request = False

        # Ustaw odpowiednią zmienną na podstawie obserwowanej wartości
        if request_value == 3:
            self.service_mode_request = True
        elif request_value == 2:
            self.dynamic_mode_request = True
        elif request_value == 0:
            self.normal_mode_request = True

    def _update_active_variables(self, command_id: int):
        """
        Aktualizuje zmienne *_active na podstawie obserwowanego command_id
        """
        # Resetuj wszystkie active variables
        self.service_mode_active = False
        self.dynamic_mode_active = False
        self.normal_mode_active = False

        # Ustaw odpowiednią zmienną na podstawie obserwowanego command_id
        if command_id == 0x0006:
            self.service_mode_active = True
        elif command_id == 0x0004:
            self.dynamic_mode_active = True
        elif command_id == 0x0003:
            self.normal_mode_active = True

    def get_current_observed_state(self) -> Optional[MachineStateEnum]:
        """
        Zwraca aktualnie obserwowany stan na podstawie zmiennych stanu
        """
        current_variables = {
            'service_mode_request': self.service_mode_request,
            'service_mode_active': self.service_mode_active,
            'dynamic_mode_request': self.dynamic_mode_request,
            'dynamic_mode_active': self.dynamic_mode_active,
            'normal_mode_request': self.normal_mode_request,
            'normal_mode_active': self.normal_mode_active
        }

        # Sprawdź który stan odpowiada aktualnym zmiennym
        for state, state_definition in self._state_definitions.items():
            if current_variables == state_definition:
                return state

        # Jeśli nie znaleziono pasującego stanu
        logger.debug(f"Obserwowane zmienne nie pasują do żadnego znanego stanu: {current_variables}")
        return MachineStateEnum.UNKNOWN_STATE

    def add_state_change_callback(self, callback: Callable[[Optional[MachineStateEnum], Optional[MachineStateEnum]], None]):
        """Dodaje callback wywoływany przy obserwacji zmiany stanu"""
        self._state_change_callbacks.append(callback)

    def remove_state_change_callback(self, callback: Callable):
        """Usuwa callback"""
        if callback in self._state_change_callbacks:
            self._state_change_callbacks.remove(callback)

    def _notify_state_change(self, old_state: Optional[MachineStateEnum], new_state: Optional[MachineStateEnum]):
        """Powiadamia wszystkie callbacki o obserwacji zmiany stanu"""
        for callback in self._state_change_callbacks:
            try:
                callback(old_state, new_state)
            except Exception as e:
                logger.error(f"Błąd w callbacku obserwacji stanu: {str(e)}")

    def get_observation_info(self) -> Dict[str, Any]:
        """Zwraca pełne informacje o obserwowanym stanie"""
        current_state = self.get_current_observed_state()
        return {
            'observed_state': current_state.value if current_state else 'UNKNOWN',
            'state_variables': {
                'service_mode_request': self.service_mode_request,
                'service_mode_active': self.service_mode_active,
                'dynamic_mode_request': self.dynamic_mode_request,
                'dynamic_mode_active': self.dynamic_mode_active,
                'normal_mode_request': self.normal_mode_request,
                'normal_mode_active': self.normal_mode_active
            },
            'network_observations': {
                'last_request_value': self._last_observed_request_value,
                'last_command_id': self._last_observed_command_id,
                'last_command_id_hex': hex(self._last_observed_command_id) if self._last_observed_command_id is not None else None
            },
            'timestamp': self._get_timestamp()
        }

    def _get_timestamp(self) -> str:
        """Zwraca aktualny timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    def is_in_observed_state(self, state: MachineStateEnum) -> bool:
        """Sprawdza czy aktualnie obserwowany stan to określony stan"""
        return self.get_current_observed_state() == state

    def get_state_variables(self) -> Dict[str, bool]:
        """Zwraca aktualne wartości wszystkich zmiennych stanu"""
        return {
            'service_mode_request': self.service_mode_request,
            'service_mode_active': self.service_mode_active,
            'dynamic_mode_request': self.dynamic_mode_request,
            'dynamic_mode_active': self.dynamic_mode_active,
            'normal_mode_request': self.normal_mode_request,
            'normal_mode_active': self.normal_mode_active
        }


# Globalna instancja observera (singleton)
machine_state_observer = MachineStateObserver()