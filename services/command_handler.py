
from fastapi import  Depends
from sqlalchemy.orm import Session
from datetime import datetime

from models.models import MeasureData
from repositories.database import get_db
from services.support import ProtocolAnalyzer, CommandID
from fastapi.responses import Response
from services.cipher import  RC4KeyGenerator


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
            CommandID.CMD_2: self._handle_cmd_2,
            CommandID.CMD_4: self._handle_cmd_4,
            CommandID.CMD_5: self._handle_cmd_5,
            CommandID.CMD_6: self._handle_cmd_6,
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
        measure_data = ProtocolAnalyzer.parse_measure_data(decoded_data)

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

        # Przygotowanie odpowiedzi
        return self._prepare_response(decoded_data, flag, status=0x01, request=0x00)

    def _handle_register_unit(self, decoded_data: bytes, flag: int, db: Session) -> Response:
        """
        Obsługa komendy CMD_0 (0x0000)
        """

        return self._prepare_response_register(decoded_data, flag, status=0x01, request=0x00)

    def _handle_cmd_1(self, decoded_data: bytes, flag: int, db: Session) -> Response:
        """
        Obsługa komendy CMD_1 (0x0001)
        """
        # TODO: Implementacja obsługi komendy
        return self._prepare_response(decoded_data, flag, status=0x01, request=0x00)

    def _handle_cmd_2(self, decoded_data: bytes, flag: int, db: Session) -> Response:
        """
        Obsługa komendy CMD_2 (0x0002)
        """
        # TODO: Implementacja obsługi komendy
        return self._prepare_response(decoded_data, flag, status=0x01, request=0x00)

    def _handle_cmd_4(self, decoded_data: bytes, flag: int, db: Session) -> Response:
        """
        Obsługa komendy CMD_4 (0x0004)
        """
        # TODO: Implementacja obsługi komendy
        return self._prepare_response(decoded_data, flag, status=0x01, request=0x00)

    def _handle_cmd_5(self, decoded_data: bytes, flag: int, db: Session) -> Response:
        """
        Obsługa komendy CMD_5 (0x0005)
        """
        # TODO: Implementacja obsługi komendy
        return self._prepare_response(decoded_data, flag, status=0x01, request=0x00)

    def _handle_cmd_6(self, decoded_data: bytes, flag: int, db: Session) -> Response:
        """
        Obsługa komendy CMD_6 (0x0006)
        """
        # TODO: Implementacja obsługi komendy
        return self._prepare_response(decoded_data, flag, status=0x01, request=0x00)

    def _handle_unknown_command(self, command_id: int) -> dict:
        """
        Obsługa nieznanych komend
        """
        return {
            "command": f"CMD_{command_id:04x}",
            "status": "not_implemented"
        }

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

        # response_data.append(0x02)  # DATA_LEN (2 bajty danych)
        # response_data.append(status)  # STATUS (1B)
        # response_data.append(request)  # REQUEST (1B)

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