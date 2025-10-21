from fastapi import Depends
from sqlalchemy.orm import Session
from datetime import datetime

# from main import config
from models.models import MeasureData, Aliases, StaticParams
from repositories.database import get_db
from services.machine_state import machine_state_observer
from services.support import ProtocolAnalyzer, CommandID
from fastapi.responses import Response
from services.cipher import RC4KeyGenerator
from services.selected_device_store import selected_device_store
from services.service_parameter_store import service_parameter_store
from services.service_mode import ServiceMode
from services.device_activity_tracker import device_activity_tracker  # NOWY IMPORT

import logging

logger = logging.getLogger(__name__)

class CommandHandler:
    """
    Klasa odpowiedzialna za obsługę komend protokołu
    """

    def __init__(self, key1: str, key2: str):
        self.key1 = key1
        self.key2 = key2

    def handle_command(self, command_id: int, decoded_data: bytes, flag: int, db: Session) -> Response:
        """
        Główna metoda obsługująca komendy na podstawie command_id
        """
        # Mapowanie command_id na odpowiednie metody
        command_handlers = {
            CommandID.MEASURE_DATA: self._handle_measure_data,
            CommandID.REGISTER_UNIT: self._handle_register_unit,
            CommandID.CMD_1: self._handle_cmd_1,
            CommandID.CAPTURE_ALIASES: self._handle_capture_aliases,
            CommandID.CAPTURE_DYNAMIC: self._handle_capture_dynamic,
            CommandID.CAPTURE_STATIC: self._handle_capture_static,
            CommandID.SERVICE_DATA: self._handle_service_data,
        }

        # Wywołanie odpowiedniej metody lub obsługa nieznanych komend
        handler = command_handlers.get(command_id)
        if handler:
            return handler(decoded_data, flag, db)
        else:
            return self._handle_unknown_command(command_id)

    def _handle_measure_data(self, decoded_data: bytes, flag: int, db: Session) -> Response:
        """
        Obsługa komendy MEASURE_DATA (0x0003)
        """
        ServiceMode.set_active(False)
        measure_data = ProtocolAnalyzer.parse_measure_data(decoded_data)

        # AKTUALIZACJA AKTYWNOŚCI URZĄDZENIA
        device_activity_tracker.update_activity(measure_data.deviceId)

        # Tworzenie nowego rekordu w bazie danych
        db_measure = MeasureData(
            deviceId=measure_data.deviceId,
            speed=measure_data.speed,
            rate=measure_data.rate,
            total=measure_data.total,
            currentTime=measure_data.currentTime
        )

        # Dodanie i zatwierdzenie w bazie danych
        db.add(db_measure)
        db.commit()

        # Pobieramy parametry z pakietu danych
        data_start = 4 + 17 + 1  # HEADER(4B) + JAWNA(17B) + DATA_LEN(1B)
        #----------dodaje stan przenosnika
        # Pobieram STATUS z odpowiedzi (jeśli dane są dostępne)
        status=0
        if len(decoded_data) > data_start:
            _status = decoded_data[data_start:data_start + 1]
            status = int.from_bytes(_status, 'big')

        # Logowanie statusu i interpretacja

        if status == 0:
           # logger.info("Tryb serwisowy jest aktywny")
           # ServiceMode.set_active(True)
           # ServiceMode.set_status_message("Tryb serwisowy aktywny")
            ServiceMode.set_conveyor_status("stopped")  # Przenośnik zatrzymany
        elif status == 1:
            #logger.info("Przenośnik w ruchu")
            #ServiceMode.set_active(False)
            #ServiceMode.set_status_message("Przenośnik w ruchu")
            ServiceMode.set_conveyor_status("running")  # Przenośnik w ruchu
        elif status == 2:
           # logger.info("Inny błąd - tryb serwisowy nieaktywny")
           # ServiceMode.set_active(False)
           # ServiceMode.set_status_message("Błąd - tryb nieaktywny")
            ServiceMode.set_conveyor_status("error")  # Błąd
        else:
           # logger.warning(f"Nieznany status: {status}")
           # ServiceMode.set_active(False)
           # ServiceMode.set_status_message(f"Nieznany status: {status}")
            ServiceMode.set_conveyor_status("unknown")  # Status nieznany
        #----------

        current_device_id = measure_data.deviceId

        # Konwertuj oba ID do stringów i usuń białe znaki

        current_id_clean = str(current_device_id).strip()


        # -- NOWA IMPLEMENTACJA Z WYKOZYSTANIEM MACHINE STATE
        if selected_device_store.is_device_selected(current_id_clean):
            machine_state_observer.observe_network_activity(command_id=0x0003)
            request = ServiceMode.get_request_value()
            mode = ServiceMode.get_request_mode()
            logger.info(f"Ustawiam request w odpowiedzi na: {request} dla: {current_device_id}")
            machine_state_observer.observe_network_activity(request_value=request)
            state = machine_state_observer.get_current_observed_state()
            logger.info(f"aktualny stan to: {state}")
            logger.info(f"aktualny request to: {request}")
            logger.info(f"aktualny request mode  to: {mode}")

        else:
            request = 0x00
            # Wyczyść urządzenie z rejestru trybu serwisowego
            selected_device_store.clear_service_mode_device()
            logger.info(f"Wymuszenie wyłączenia trybu serwisowego, request:{request} dla: {current_device_id}")


        return self._prepare_response(decoded_data, flag, status=0x01, request=request)



    def _handle_register_unit(self, decoded_data: bytes, flag: int, db: Session) -> Response:
        """
        Obsługa komendy CMD_0 (0x0000)
        """
        # Przygotowanie odpowiedzi z uwzględnieniem trybu serwisowego
        try:
           request = ServiceMode.get_request_value()
        except Exception as e:
            logger.error(f"Błąd pobierania request_value z ServiceMode: {e}")
            # Fallback - domyślna wartość
            #request = 0x03 if ServiceMode.is_enabled() else 0x00
            # z poziomu rejestracji nie mozna przejsc do service mode
            request = 0x00 if ServiceMode.is_enabled() else 0x00

        return self._prepare_response_register(decoded_data, flag, status=0x01, request=request)

    def _handle_cmd_1(self, decoded_data: bytes, flag: int, db: Session) -> Response:
        """
        Obsługa komendy CMD_1 (0x0001)
        """
        # Przygotowanie odpowiedzi z uwzględnieniem trybu serwisowego
        request_value = ServiceMode.get_request_value()
        return self._prepare_response(decoded_data, flag, status=0x01, request=request_value)

    def _handle_capture_aliases(self, decoded_data: bytes, flag: int, db: Session) -> Response:
        """
        Obsługa komendy CAPTURE_ALIASES (0x0002)
        """
        alias_data = ProtocolAnalyzer.parse_alias_data(decoded_data)
        # Sprawdź czy alias dla tego deviceId już istnieje
        existing_alias = db.query(Aliases).filter(Aliases.deviceId == alias_data.deviceId).first()

        if existing_alias:
            # Aktualizuj istniejący rekord
            existing_alias.company = alias_data.company
            existing_alias.location = alias_data.location
            existing_alias.productName = alias_data.productName
            existing_alias.scaleId = alias_data.scaleId
            # Opcjonalnie dodaj timestamp aktualizacji
            # existing_alias.updated_at = datetime.now()

            logger.info(f"Zaktualizowano alias dla deviceId: {alias_data.deviceId}")
        else:
            # Utwórz nowy rekord
            existing_alias = Aliases(
                deviceId=alias_data.deviceId,
                company=alias_data.company,
                location=alias_data.location,
                productName=alias_data.productName,
                scaleId=alias_data.scaleId
            )
            db.add(existing_alias)
            logger.info(f"Utworzono nowy alias dla deviceId: {alias_data.deviceId}")

            # Zatwierdzenie w bazie danych
        db.commit()

        # Przygotowanie odpowiedzi z uwzględnieniem trybu serwisowego
        request_value = ServiceMode.get_request_value()
        return self._prepare_response(decoded_data, flag, status=0x01, request=request_value)

    def _handle_capture_dynamic(self, decoded_data: bytes, flag: int, db: Session) -> Response:
        """
        Obsługa komendy CMD_4 (0x0004)
        """
        # Przygotowanie odpowiedzi z uwzględnieniem trybu serwisowego
        try:
            request = ServiceMode.get_request_value()
        except Exception as e:
            logger.error(f"Błąd pobierania request_value z ServiceMode: {e}")
            # Fallback - domyślna wartość
            request = 0x03 if ServiceMode.is_enabled() else 0x00

        dynamic_data = ProtocolAnalyzer.parse_dynamic_data(decoded_data)
        logger.info(f"request is set to: {request}")
        return self._prepare_response(decoded_data, flag, status=0x01, request=request)

    def _handle_capture_static(self, decoded_data: bytes, flag: int, db: Session) -> Response:
        """
        Obsługa komendy CAPTURE_STATIC (0x0005)
        """
        static_data = ProtocolAnalyzer.parse_static_data(decoded_data)
        # Sprawdź czy parametry statyczne dla tego deviceId już istnieją
        existing_static = db.query(StaticParams).filter(StaticParams.deviceId == static_data.deviceId).first()

        if existing_static:
            # Aktualizuj istniejący rekord
            existing_static.filterRate = static_data.filterRate
            existing_static.scaleCapacity = static_data.scaleCapacity
            existing_static.autoZero = static_data.autoZero
            existing_static.deadBand = static_data.deadBand
            existing_static.scaleType = static_data.scaleType
            existing_static.loadcellSet = static_data.loadcellSet
            existing_static.loadcellCapacity = static_data.loadcellCapacity
            existing_static.trimm = static_data.trimm
            existing_static.idlerSpacing = static_data.idlerSpacing
            existing_static.speedSource = static_data.speedSource
            existing_static.wheelDiameter = static_data.wheelDiameter
            existing_static.pulsesPerRev = static_data.pulsesPerRev
            existing_static.beltLength = static_data.beltLength
            existing_static.beltLengthPulses = static_data.beltLengthPulses
            existing_static.currentTime = static_data.currentTime
            # Opcjonalnie dodaj timestamp aktualizacji
            # existing_static.updated_at = datetime.now()

            logger.info(f"Zaktualizowano parametry statyczne dla deviceId: {static_data.deviceId}")
        else:
            # Utwórz nowy rekord
            existing_static = StaticParams(
                deviceId=static_data.deviceId,
                filterRate=static_data.filterRate,
                scaleCapacity=static_data.scaleCapacity,
                autoZero=static_data.autoZero,
                deadBand=static_data.deadBand,
                scaleType=static_data.scaleType,
                loadcellSet=static_data.loadcellSet,
                loadcellCapacity=static_data.loadcellCapacity,
                trimm=static_data.trimm,
                idlerSpacing=static_data.idlerSpacing,
                speedSource=static_data.speedSource,
                wheelDiameter=static_data.wheelDiameter,
                pulsesPerRev=static_data.pulsesPerRev,
                beltLength=static_data.beltLength,
                beltLengthPulses=static_data.beltLengthPulses,
                currentTime=static_data.currentTime
            )
            db.add(existing_static)
            logger.info(f"Utworzono nowe parametry statyczne dla deviceId: {static_data.deviceId}")

        # Zatwierdzenie w bazie danych

        db.commit()

        # Przygotowanie odpowiedzi z uwzględnieniem trybu serwisowego
        request_value = ServiceMode.get_request_value()
        return self._prepare_response(decoded_data, flag, status=0x01, request=request_value)



    def _handle_unknown_command(self, command_id: int) -> dict:
        """
        Obsługa nieznanych komend
        """
        return {
            "command": f"CMD_{command_id:04x}",
            "status": "not_implemented"
        }

    def _handle_service_data(self, decoded_data: bytes, flag: int, db: Session, param_address: int = 0,
                             param_data: str = "") -> Response:
        """
        Obsługa komendy SERVICE_DATA (0x0006)
        Odpowiedź zawiera:
        DATA[0] – pole Status
        DATA[1] – pole Request
        DATA[2] – pole Adres Parametru, 1B
        DATA[3-21] – pole Dane Parametru, 19B

        Parametry param_address i param_data mogą pochodzić z:
        1. Argumentów funkcji (dla wywołań testowych)
        2. ServiceParameterStore (dla rzeczywistych wywołań z kontrolera)


        Args:
            decoded_data: Dekodowane dane pakietu
            flag: Flaga szyfrowania
            db: Sesja bazy danych
            param_address: Adres parametru (domyślnie 0)
            param_data: Dane parametru jako string (domyślnie pusty)
        """

        ServiceMode.set_active(True)
        # Importy lokalne żeby uniknąć cykli importów
        from services.selected_device_store import selected_device_store

        # Pobierz device_id z pakietu

        try:
            current_device_id = decoded_data[4:14].decode('ascii').rstrip('\x00')
        except Exception as e:
            logger.error(f"Błąd dekodowania device_id z pakietu: {e}")
            current_device_id = ""

            # AKTUALIZACJA AKTYWNOŚCI URZĄDZENIA
            device_activity_tracker.update_activity(current_device_id)

        current_id_clean = str(current_device_id).strip()

        if service_parameter_store.has_parameters():
            stored_device_id, stored_param_address, stored_param_data = service_parameter_store.get_parameters()
            stored_id_clean = str(stored_device_id).strip()

            if stored_id_clean == current_id_clean:
                param_address = stored_param_address
                param_data = stored_param_data
                logger.info(f"Wykorzystano parametry ze store: address={param_address}, data='{param_data}'")

        # Wyczyść store po wykorzystaniu
                service_parameter_store.clear_parameters()
            else:
                logger.warning(f"Device ID się nie zgadza: store={stored_device_id}, pakiet={current_device_id}")


        # -- NOWA IMPLEMENTACJA Z WYKOZYSTANIEM MACHINE STATE
        if selected_device_store.is_device_selected(current_id_clean):
            machine_state_observer.observe_network_activity(command_id=0x0006)
            request = ServiceMode.get_request_value()
            logger.info(f"Ustawiam request w odpowiedzi na: {request} dla: {current_device_id}")
            machine_state_observer.observe_network_activity(request_value=request)
            state = machine_state_observer.get_current_observed_state()
            logger.info(f"aktualny stan to: {state}")
        else:
            request = 0x00
            # Wyczyść urządzenie z rejestru trybu serwisowego
            selected_device_store.clear_service_mode_device()
            logger.info(f"Wymuszenie wyłączenia trybu serwisowego, request:{request} dla: {current_device_id}")





        # Pobieramy parametry z pakietu danych
        data_start = 4 + 17 + 1  # HEADER(4B) + JAWNA(17B) + DATA_LEN(1B)

        # Status zawsze 0x01 (domyślny)
        status = 0x01





        # Ustawianie adresu parametru - używamy przekazanego parametru lub domyślnego
        param_address_byte = param_address if param_address > 0 else 0x00

        # Przygotowanie danych parametru (19 bajtów)
        param_data_bytes = bytearray(19)

        #if param_data:
        if param_data and param_data != "DISABLE_SERVICE_MODE":


            # Konwersja przekazanego stringa na bytearray(pomijamy specjalną komendę)
            param_data_str = str(param_data)
            param_data_encoded = bytearray(param_data_str.encode('ascii'))

            # Upewniamy się, że długość to dokładnie 19 bajtów
            if len(param_data_encoded) < 19:
                # Uzupełniamy spacjami, jeśli jest za krótki
                param_data_encoded.extend([0x20] * (19 - len(param_data_encoded)))
            elif len(param_data_encoded) > 19:
                # Obcinamy, jeśli jest za długi
                param_data_encoded = param_data_encoded[:19]

            param_data_bytes = param_data_encoded
        else:
            # Domyślne dane - wypełniamy pustymi znakami (spacje)
            for i in range(19):
                param_data_bytes[i] = 0x20  # Kod ASCII spacji

        # W zależności od adresu parametru, możemy dodać dodatkową logikę
        if param_address_byte > 0 and param_address_byte <= 15:
            # Logika dla konkretnych parametrów

            logger.info(f"Obsługa parametru serwisowego - adres: {param_address_byte}, dane: {param_data}")

        # Pobieram STATUS z odpowiedzi (jeśli dane są dostępne)
        if len(decoded_data) > data_start:
            _status = decoded_data[data_start:data_start + 1]
            status = int.from_bytes(_status, 'big')

        # Logowanie statusu i interpretacja


        if status == 0:
            logger.info("Tryb serwisowy jest aktywny")
            ServiceMode.set_active(True)
            ServiceMode.set_status_message("Tryb serwisowy aktywny")
            ServiceMode.set_conveyor_status("stopped")  # Przenośnik zatrzymany
        elif status == 1:
            logger.info("Przenośnik w ruchu")
            ServiceMode.set_active(False)
            ServiceMode.set_status_message("Przenośnik w ruchu")
            ServiceMode.set_conveyor_status("running")  # Przenośnik w ruchu
        elif status == 2:
            logger.info("Inny błąd - tryb serwisowy nieaktywny")
            ServiceMode.set_active(False)
            ServiceMode.set_status_message("Błąd - tryb nieaktywny")
            ServiceMode.set_conveyor_status("error")  # Błąd
        else:
            logger.warning(f"Nieznany status: {status}")
            ServiceMode.set_active(False)
            ServiceMode.set_status_message(f"Nieznany status: {status}")
            ServiceMode.set_conveyor_status("unknown")  # Status nieznany

            # Logowanie wartości request dla debugowania
        request_mode = ServiceMode.get_request_mode()
        logger.info(f"Tryb żądania: {request_mode}, wartość request: 0x{request:02X}")

        if request == 0x02:
            logger.info("Zewnętrzny kontroler zostanie przełączony na dynamiczne przesyłanie danych (0x0004)")
        elif request == 0x03:
            logger.info("Tryb serwisowy będzie podtrzymany")
        elif request == 0x00:
            logger.info("Zewnętrzny kontroler wyjdzie z trybu serwisowego")

        # Pobieramy DEVICE_ID i COMMAND_ID z sekcji JAWNA
        _device_id = decoded_data[4:14]  # 10 bajtów
        _command_id = decoded_data[14:16]  # 2 bajty

        # Ustawienie najstarszego bitu w COMMAND_ID
        command_id_value = int.from_bytes(_command_id, 'big')
        command_id_value |= 0x8000
        _command_id = command_id_value.to_bytes(2, 'big')

        response_data = bytearray()

        # HEADER (4B)
        response_data.extend([0xAA, 0x55])  # START_MARKER_1 i START_MARKER_2
        response_data.append(0x01)  # VERSION
        response_data.append(0x00)  # FLAGS (plain)

        # JAWNA (17B)
        response_data.extend(_device_id)  # DEVICE_ID (10B)
        response_data.extend(_command_id)  # COMMAND_ID (2B)
        response_data.append(0x00)  # RC4_KEY_ID (1B)
        response_data.extend(b'\x00\x00\x00')  # TIMESTAMP (3B)
        response_data.append(0x00)  # SEQ_NUM (1B)

        # SZYFROWANA
        response_data.append(22)  # DATA_LEN (22 bajty danych: Status+Request+Adres+Dane)
        response_data.append(status)  # STATUS (1B)
        response_data.append(request)  # REQUEST (1B)
        response_data.append(param_address_byte)  # Adres parametru (1B)
        response_data.extend(param_data_bytes)  # Dane parametru (19B)

        # Obliczenie CRC8 dla sekcji SZYFROWANA
        crc8 = ProtocolAnalyzer.calculate_crc8(response_data[-23:])  # dla DATA_LEN + DATA
        response_data.append(crc8)
        encrypted_segment = response_data[21:]

        # Jeśli flaga encode = true koduje dane
        if (flag & 0x01):
            response_data[3] = 1
            cipher = RC4KeyGenerator.create_cipher(self.key1, self.key2)
            encrypted = cipher.encrypt(encrypted_segment)
            response_data[21:] = encrypted

        # Obliczenie CRC16 dla całości (bez znacznika końca)
        crc16 = ProtocolAnalyzer.calculate_crc16(response_data)
        response_data.extend(crc16.to_bytes(2, 'big'))  # CRC16 (2B)

        # FOOTER - znacznik końca
        response_data.append(0x55)  # END_MARKER (1B)

        return Response(content=bytes(response_data), media_type="application/octet-stream")

    def _prepare_response(self, decoded_data: bytes, flag: int, status: int, request: int) -> Response:
        """
        Przygotowanie standardowej odpowiedzi na komendę
        """
        # Pobieramy DEVICE_ID i COMMAND_ID z sekcji JAWNA
        _device_id = decoded_data[4:14]  # 10 bajtów
        _command_id = decoded_data[14:16]  # 2 bajty

        # Ustawienie najstarszego bitu w COMMAND_ID
        command_id_value = int.from_bytes(_command_id, 'big')
        command_id_value |= 0x8000
        _command_id = command_id_value.to_bytes(2, 'big')

        response_data = bytearray()

        # HEADER (4B)
        response_data.extend([0xAA, 0x55])  # START_MARKER_1 i START_MARKER_2
        response_data.append(0x01)  # VERSION
        response_data.append(0x00)  # FLAGS (plain)

        # JAWNA (17B)
        response_data.extend(_device_id)  # DEVICE_ID (10B)
        response_data.extend(_command_id)  # COMMAND_ID (2B)
        response_data.append(0x00)  # RC4_KEY_ID (1B)
        response_data.extend(b'\x00\x00\x00')  # TIMESTAMP (3B)
        response_data.append(0x00)  # SEQ_NUM (1B)

        # SZYFROWANA
        response_data.append(0x02)  # DATA_LEN (2 bajty danych)
        response_data.append(status)  # STATUS (1B)
        response_data.append(request)  # REQUEST (1B)

        # Obliczenie CRC8 dla sekcji SZYFROWANA
        crc8 = ProtocolAnalyzer.calculate_crc8(response_data[-4:])  # dla DATA_LEN + DATA
        response_data.append(crc8)
        encrypted_segment = response_data[21:]

        # Jeśli flaga encode = true koduje dane
        if (flag & 0x01):
            response_data[3] = 1
            cipher = RC4KeyGenerator.create_cipher(self.key1, self.key2)
            encrypted = cipher.encrypt(encrypted_segment)
            response_data[21:] = encrypted

        # Obliczenie CRC16 dla całości (bez znacznika końca)
        crc16 = ProtocolAnalyzer.calculate_crc16(response_data)
        response_data.extend(crc16.to_bytes(2, 'big'))  # CRC16 (2B)

        # FOOTER - znacznik końca
        response_data.append(0x55)  # END_MARKER (1B)

        return Response(content=bytes(response_data), media_type="application/octet-stream")

    def _prepare_response_register(self, decoded_data: bytes, flag: int, status: int, request: int) -> Response:
        """
        Przygotowanie standardowej odpowiedzi na komendę
        """
        # Pobieramy DEVICE_ID i COMMAND_ID z sekcji JAWNA
        _device_id = decoded_data[4:14]  # 10 bajtów
        _command_id = decoded_data[14:16]  # 2 bajty

        # Ustawienie najstarszego bitu w COMMAND_ID
        command_id_value = int.from_bytes(_command_id, 'big')
        command_id_value |= 0x8000
        _command_id = command_id_value.to_bytes(2, 'big')

        response_data = bytearray()

        # HEADER (4B)
        response_data.extend([0xAA, 0x55])  # START_MARKER_1 i START_MARKER_2
        response_data.append(0x01)  # VERSION
        response_data.append(0x00)  # FLAGS (plain)

        # JAWNA (17B)
        response_data.extend(_device_id)  # DEVICE_ID (10B)
        response_data.extend(_command_id)  # COMMAND_ID (2B)
        response_data.append(0x00)  # RC4_KEY_ID (1B)
        response_data.extend(b'\x00\x00\x00')  # TIMESTAMP (3B)
        response_data.append(0x00)  # SEQ_NUM (1B)

        # SZYFROWANA
        # Pobieramy aktualny czas
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Zwiększamy DATA_LEN o 19 bajtów (dla daty)
        response_data.append(0x15)  # DATA_LEN (2 + 19 bajty danych: 2 bajty oryginalnych danych + 19 bajtów daty)
        response_data.append(status)  # STATUS (1B)
        response_data.append(request)  # REQUEST (1B)
        # Dodajemy 19 bajtów z aktualną datą i czasem
        response_data.extend(current_time.encode('ascii'))  # Data i czas w formacie ASCII (19B)

        # Obliczenie CRC8 dla sekcji SZYFROWANA
        crc8 = ProtocolAnalyzer.calculate_crc8(response_data[-22:])  # dla DATA_LEN + DATA
        response_data.append(crc8)
        encrypted_segment = response_data[21:]

        # Jeśli flaga encode = true koduje dane
        if (flag & 0x01):
            response_data[3] = 1
            cipher = RC4KeyGenerator.create_cipher(self.key1, self.key2)
            encrypted = cipher.encrypt(encrypted_segment)
            response_data[21:] = encrypted

        # Obliczenie CRC16 dla całości (bez znacznika końca)
        crc16 = ProtocolAnalyzer.calculate_crc16(response_data)
        response_data.extend(crc16.to_bytes(2, 'big'))  # CRC16 (2B)

        # FOOTER - znacznik końca
        response_data.append(0x55)  # END_MARKER (1B)

        return Response(content=bytes(response_data), media_type="application/octet-stream")


# Funkcja opakowująca dla zachowania wstecznej kompatybilności
def command_support(command_id: int, decoded_data: bytes, flag: int, key1: str, key2: str,
                    db: Session = Depends(get_db)):
    """
    Funkcja opakowująca dla zachowania wstecznej kompatybilności.
    Deleguje obsługę do instancji CommandHandler.
    """
    handler = CommandHandler(key1, key2)
    return handler.handle_command(command_id, decoded_data, flag, db)
