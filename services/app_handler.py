from pydantic import BaseModel
from typing import Dict, Any, Optional, Union
from datetime import datetime
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from models.models import StaticParams
import logging

# Logger dla modułu
logger = logging.getLogger(__name__)


# Zmienne globalne dla adresów parametrów
class ParameterAddresses:
    DUMMY = 0
    FILTER_RATE = 1
    SCALE_CAPACITY = 2
    AUTO_ZERO = 3
    DEAD_BAND = 4
    SCALE_TYPE = 5
    LOAD_CELLS_SET = 6
    LOADCELL_CAPACITY = 7
    TRIMM = 8
    IDLER_SPACING = 9
    SPEED_SOURCE = 10
    WHEEL_DIAMETER = 11
    PULSES_PER_REV = 12
    BELT_LENGTH = 13
    BELT_LENGTH_PULSES = 14
    CURRENT_TIME = 15


# Definicje formatów danych dla różnych parametrów
class ParameterFormats:
    ONE_BYTE = "1B"  # Pojedynczy bajt dla wartości 0-9
    EIGHT_BYTES = "8B"  # 8 bajtów dla wartości float/int
    TIME_FORMAT = "19B"  # Format czasu "YYYY-MM-DD HH:MM:SS"


# Mapowanie adresów parametrów na ich nazwy i formaty
PARAMETER_MAPPING = {
    ParameterAddresses.DUMMY: {"name": "dummy", "format": ParameterFormats.ONE_BYTE},
    ParameterAddresses.FILTER_RATE: {"name": "filterRate", "format": ParameterFormats.ONE_BYTE},
    ParameterAddresses.SCALE_CAPACITY: {"name": "scaleCapacity", "format": ParameterFormats.EIGHT_BYTES},
    ParameterAddresses.AUTO_ZERO: {"name": "autoZero", "format": ParameterFormats.EIGHT_BYTES},
    ParameterAddresses.DEAD_BAND: {"name": "deadBand", "format": ParameterFormats.EIGHT_BYTES},
    ParameterAddresses.SCALE_TYPE: {"name": "scaleType", "format": ParameterFormats.ONE_BYTE},
    ParameterAddresses.LOAD_CELLS_SET: {"name": "loadcellSet", "format": ParameterFormats.ONE_BYTE},
    ParameterAddresses.LOADCELL_CAPACITY: {"name": "loadcellCapacity", "format": ParameterFormats.EIGHT_BYTES},
    ParameterAddresses.TRIMM: {"name": "trimm", "format": ParameterFormats.EIGHT_BYTES},
    ParameterAddresses.IDLER_SPACING: {"name": "idlerSpacing", "format": ParameterFormats.EIGHT_BYTES},
    ParameterAddresses.SPEED_SOURCE: {"name": "speedSource", "format": ParameterFormats.ONE_BYTE},
    ParameterAddresses.WHEEL_DIAMETER: {"name": "wheelDiameter", "format": ParameterFormats.EIGHT_BYTES},
    ParameterAddresses.PULSES_PER_REV: {"name": "pulsesPerRev", "format": ParameterFormats.EIGHT_BYTES},
    ParameterAddresses.BELT_LENGTH: {"name": "beltLength", "format": ParameterFormats.EIGHT_BYTES},
    ParameterAddresses.BELT_LENGTH_PULSES: {"name": "beltLengthPulses", "format": ParameterFormats.EIGHT_BYTES},
    ParameterAddresses.CURRENT_TIME: {"name": "currentTime", "format": ParameterFormats.TIME_FORMAT},
}


class ServiceParameterRequest(BaseModel):
    """Model dla żądania aktualizacji parametru serwisowego"""
    device_id: str
    param_address: int
    param_data: str


class ApplicationHandler:
    """
    Klasa odpowiedzialna za obsługę żądań z aplikacji komputerowej.
    Jest to osobna klasa od CommandHandler, która zajmuje się tylko komunikacją z frontendem.
    """

    def __init__(self):
        """Inicjalizacja handlera aplikacji"""
        pass

    def format_parameter_value(self, param_address: int, value: str) -> str:
        """
        Formatuje wartość parametru zgodnie z jego formatem

        Args:
            param_address: Adres parametru
            value: Wartość parametru do sformatowania

        Returns:
            str: Sformatowana wartość parametru
        """
        if param_address not in PARAMETER_MAPPING:
            logger.warning(f"Nieznany adres parametru: {param_address}")
            return value

        param_format = PARAMETER_MAPPING[param_address]["format"]

        # Formatowanie zgodnie z typem parametru
        if param_format == ParameterFormats.ONE_BYTE:
            # Dla parametrów 1-bajtowych upewniamy się, że mamy pojedynczą cyfrę
            return value[-1:] if value else "0"
        elif param_format == ParameterFormats.EIGHT_BYTES:
            # Dla parametrów 8-bajtowych przycinamy/wypełniamy do 8 znaków
            formatted = value.ljust(8)[:8]
            return formatted
        elif param_format == ParameterFormats.TIME_FORMAT:
            # Dla formatu czasu używamy pełnych 19 znaków
            if len(value) != 19:
                # Jeśli nie przekazano prawidłowego formatu, używamy bieżącego czasu
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return current_time
            return value

        return value

    def validate_parameter(self, param_address: int, param_data: str) -> bool:
        """
        Sprawdza poprawność danych parametru

        Args:
            param_address: Adres parametru
            param_data: Dane parametru

        Returns:
            bool: True jeśli dane są poprawne, False w przeciwnym razie
        """
        if param_address not in PARAMETER_MAPPING:
            logger.warning(f"Nieznany adres parametru: {param_address}")
            return False

        param_format = PARAMETER_MAPPING[param_address]["format"]

        # Walidacja w zależności od formatu parametru
        if param_format == ParameterFormats.ONE_BYTE:
            # Dla parametrów 1-bajtowych sprawdzamy czy to liczba 0-9
            if not param_data or not param_data[-1:].isdigit():
                return False
        elif param_format == ParameterFormats.EIGHT_BYTES:
            # Dla parametrów 8-bajtowych na razie tylko sprawdzamy długość
            if len(param_data) > 8:
                return False
        elif param_format == ParameterFormats.TIME_FORMAT:
            # Dla czasu sprawdzamy format
            if len(param_data) != 19:
                return False
            try:
                datetime.strptime(param_data, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return False

        return True

    def update_parameter(self, device_id: str, param_address: int, param_data: str, db: Session) -> Dict[str, Any]:
        """
        Aktualizuje parametr w bazie danych

        Args:
            device_id: ID urządzenia
            param_address: Adres parametru
            param_data: Nowa wartość parametru
            db: Sesja bazy danych

        Returns:
            Dict[str, Any]: Wynik operacji
        """
        # Walidacja parametru
        if not self.validate_parameter(param_address, param_data):
            return {
                "status": "error",
                "message": f"Niepoprawny format danych dla parametru {param_address}"
            }

        # Formatowanie wartości
        formatted_value = self.format_parameter_value(param_address, param_data)

        try:
            # Pobierz najnowszy rekord dla urządzenia
            device_params = db.query(StaticParams).filter(StaticParams.deviceId == device_id).order_by(
                StaticParams.id.desc()).first()

            if not device_params:
                return {"status": "error", "message": f"Nie znaleziono urządzenia o ID {device_id}"}

            # Aktualizacja odpowiedniego parametru
            if param_address in PARAMETER_MAPPING:
                param_name = PARAMETER_MAPPING[param_address]["name"]
                setattr(device_params, param_name, formatted_value)

                db.commit()
                logger.info(f"Zaktualizowano parametr {param_name} dla urządzenia {device_id}")

                return {
                    "status": "success",
                    "message": f"Parametr {param_name} zaktualizowany",
                    "value": formatted_value
                }
            else:
                return {"status": "error", "message": f"Nieznany adres parametru: {param_address}"}

        except Exception as e:
            db.rollback()
            logger.error(f"Błąd podczas aktualizacji parametru: {str(e)}")
            return {"status": "error", "message": f"Błąd bazy danych: {str(e)}"}

    def get_device_parameters(self, device_id: str, db: Session) -> Dict[str, Any]:
        """
        Pobiera wszystkie parametry dla urządzenia

        Args:
            device_id: ID urządzenia
            db: Sesja bazy danych

        Returns:
            Dict[str, Any]: Słownik zawierający wszystkie parametry urządzenia
        """
        try:
            # Pobierz najnowszy rekord dla urządzenia
            device_params = db.query(StaticParams).filter(StaticParams.deviceId == device_id).order_by(
                StaticParams.id.desc()).first()

            if not device_params:
                return {"status": "error", "message": f"Nie znaleziono urządzenia o ID {device_id}"}

            # Przygotuj słownik z parametrami
            result = {"status": "success", "device_id": device_id, "parameters": {}}

            # Dodaj wszystkie parametry
            for addr, info in PARAMETER_MAPPING.items():
                param_name = info["name"]
                if hasattr(device_params, param_name):
                    result["parameters"][addr] = {
                        "name": param_name,
                        "value": getattr(device_params, param_name),
                        "format": info["format"]
                    }

            return result

        except Exception as e:
            logger.error(f"Błąd podczas pobierania parametrów: {str(e)}")
            return {"status": "error", "message": f"Błąd bazy danych: {str(e)}"}

    def get_parameter(self, device_id: str, param_address: int, db: Session) -> Dict[str, Any]:
        """
        Pobiera wartość konkretnego parametru dla urządzenia

        Args:
            device_id: ID urządzenia
            param_address: Adres parametru
            db: Sesja bazy danych

        Returns:
            Dict[str, Any]: Słownik z wartością parametru
        """
        try:
            # Pobierz najnowszy rekord dla urządzenia
            device_params = db.query(StaticParams).filter(StaticParams.deviceId == device_id).order_by(
                StaticParams.id.desc()).first()

            if not device_params:
                return {"status": "error", "message": f"Nie znaleziono urządzenia o ID {device_id}"}

            # Sprawdź czy parametr istnieje
            if param_address in PARAMETER_MAPPING:
                param_name = PARAMETER_MAPPING[param_address]["name"]
                param_format = PARAMETER_MAPPING[param_address]["format"]

                if hasattr(device_params, param_name):
                    return {
                        "status": "success",
                        "device_id": device_id,
                        "parameter": {
                            "address": param_address,
                            "name": param_name,
                            "value": getattr(device_params, param_name),
                            "format": param_format
                        }
                    }

            return {"status": "error", "message": f"Nieznany parametr o adresie {param_address}"}

        except Exception as e:
            logger.error(f"Błąd podczas pobierania parametru: {str(e)}")
            return {"status": "error", "message": f"Błąd bazy danych: {str(e)}"}