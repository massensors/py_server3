from enum import IntEnum
from pydantic import BaseModel
from models.models import MeasureData, Aliases
from fastapi.responses import Response
from fastapi import  Depends
from sqlalchemy.orm import Session
from repositories.database import get_db
import hashlib
from Crypto.Cipher import ARC4
from crc import Calculator, Configuration
from services.cipher import  RC4KeyGenerator
import logging

from services.dynamic_mode import dynamic_readings_store

# Logger dla modułu
logger = logging.getLogger(__name__)


CRC8_CONFIG = Configuration(
    width=8,
    polynomial=0x07,
    init_value=0x00,
    final_xor_value=0x00,
    reverse_input=False,
    reverse_output=False
)

BYTE_CHECKSUM_CONFIG = Configuration(
    width=8,          # 8 bitów
    polynomial=0x00,  # brak wielomianu (nie jest używany w sumie bajtów)
    init_value=0x00,  # wartość początkowa 0
    final_xor_value=0x00,  # brak końcowego XORowania
    reverse_input=False,
    reverse_output=False,
   # is_byte_sum=True  # To jest kluczowy parametr - włącza tryb sumy bajtów
)


# Utworzenie kalkulatora CRC8





CRC16_CCITT_CONFIG = Configuration(
    width=16,
    polynomial=0x1021,
    init_value=0xFFFF,
    final_xor_value=0x0000,
    reverse_input=False,
    reverse_output=False
)





class CommandID(IntEnum):
    """
    Dostępne komendy protokołu
    """
    REGISTER_UNIT = 0x0000
    CMD_1 = 0x0001
    CAPTURE_ALIASES = 0x0002
    MEASURE_DATA = 0x0003  # Komenda do przesyłania danych pomiarowych
    CAPTURE_DYNAMIC = 0x0004
    CAPTURE_STATIC = 0x0005
    SERVICE_DATA = 0x0006


class MeasureDataPayload(BaseModel):
    """
    Model danych dla komendy MEASURE_DATA (0x0003)
    """

    status: int
    request: int
    deviceId: str
    speed: str
    rate: str
    total: str
    currentTime: str


class AliasDataPayload(BaseModel):
    """
    Model danych dla komendy ALIAS_DATA (0x0002)
    """
    deviceId: str
    company: str
    location: str
    productName: str
    scaleId: str

class StaticDataPayload(BaseModel):
    """
    Model danych dla komendy ALIAS_DATA (0x0002)
    """
    deviceId: str
    filterRate: str
    scaleCapacity: str
    autoZero: str
    deadBand: str
    scaleType: str
    loadcellSet: str
    loadcellCapacity: str
    trimm : str
    idlerSpacing: str
    speedSource: str
    wheelDiameter: str
    pulsesPerRev: str
    beltLength: str
    beltLengthPulses: str
    currentTime: str


class ProtocolAnalyzer:
    """
    Analizator protokołu
    """

    @staticmethod
    def validate_frame(data: bytes) -> bool:
        """
        Sprawdza podstawową poprawność ramki
        """
        if len(data) < 3 or data[-1] != 0x55:
            return False

        # Obliczanie i weryfikacja CRC16
        received_crc = int.from_bytes(data[-3:-1], 'big')
        calculated_crc = ProtocolAnalyzer.calculate_crc16(data[:-3])

        #calculated_crc = calculator.checksum(data[:-3])

        return received_crc == calculated_crc

    # ---sha 256
    @staticmethod
    def _calculate_key(key1: str, key2: str, iterations: int) -> bytes:
        """
        Oblicza klucz na podstawie key1 i key2 wykonując iterations iteracji SHA256
         key = SHA256(key . key1 . key2)

        Args:
            key1: Pierwszy klucz (string)
            key2: Drugi klucz (string)
            iterations: Liczba iteracji

        Returns:
             bytes: 32-bajtowy klucz końcowy
         """
        # Początkowa konkatenacja kluczy
        key = key1 + key2

        # Wykonanie określonej liczby iteracji
        for _ in range(iterations):
            # W każdej iteracji: key = SHA256(key . key1 . key2)
            combined = (key + key1 + key2).encode()
            key = hashlib.sha256(combined).hexdigest()

        # Zwracamy ostateczny klucz jako bytes
        return bytes.fromhex(key)

    # ---sha 256 koniec
    # ----wstawione dane

    # --- nowa implementacja cipher
    # --- koniec nowej implementacji cipher
    @staticmethod
   # def encode_data(data: bytes, iterations: int, Key1:bytes, Key2:bytes) -> tuple[bytes, bool]:

    def encode_data(data: bytes, iterations: int, Key1: str, Key2: str) -> tuple[bytes, bool]:
        """
    Koduje dane zgodnie z flagą w HEADER i weryfikuje CRC8.

    Args:
        data: Strumień bajtów do przetworzenia
        iterations: Liczba iteracji dla kodowania
        key = SHA256 (key . key1 . key2)
        key1: Klucz kodowania z argumentu
        key2: Klucz kodowania z argumentu

    Returns:
        tuple[bytes, bool]: (Przetworzone dane, Czy weryfikacja CRC8 się powiodła)
    """
        try:
            # Sprawdzenie minimalnej długości danych
            if len(data) < 4:
                raise ValueError("Dane są zbyt krótkie - brak HEADER")

            # Pobranie flagi z HEADER (4-ty bajt)
            flags = data[3]

            # Wyodrębnienie segmentu SZYFROWANA
            encrypted_segment_start = 4 + 17  # HEADER(4B) + JAWNA(17B)
            encrypted_segment = data[encrypted_segment_start:-3]  # Bez FOOTER
            header = data[:3]
            plain = data[3:21]
            #footer = data[-3:]

            if len(encrypted_segment) < 2:  # Minimum to DATA_LEN(1B) + CRC8(1B)
                raise ValueError("Segment SZYFROWANA jest zbyt krótki")

            # Pobranie długości danych i CRC8
            #data_len = encrypted_segment[0]
            received_crc8 = encrypted_segment[-1]

            # Wyodrębnienie właściwych danych
            #actual_data = encrypted_segment[1:-1]

            if (flags & 0x01) == 0:  # IntegratorProtocol.ProtocolFlags.PLAIN.value:
                # Dla danych niezaszyfrowanych tylko weryfikujemy CRC8
                #data_to_check = bytes([data_len]) + actual_data
                calculated_crc8 = ProtocolAnalyzer.calculate_crc8(encrypted_segment[:-1])
                return data, received_crc8 == calculated_crc8

            elif (flags & 0x01) == 1:  # IntegratorProtocol.ProtocolFlags.ENCRYPTED.value:
                # Dla danych zaszyfrowanych
                # 1. Inicjalizacja RC4
                #key = ProtocolAnalyzer._calculate_key(key1, key2, iterations)
                #cipher = ARC4.new(key)

                # 2. Odszyfrowanie zakodowanej czesci z danymi
                #decrypted_segment = cipher.decrypt(encrypted_segment)
                cipher = RC4KeyGenerator.create_cipher(Key1, Key2, iterations)
               # cipher = RC4KeyGenerator.create_cipher(Key1)
                decrypted_segment = cipher.decrypt(encrypted_segment)

                # 3. Weryfikacja CRC8
                # data_to_check = bytes([data_len]) + decrypted_data
                calculated_crc8 = ProtocolAnalyzer.calculate_crc8(decrypted_segment[:-1])
                received_crc8 = decrypted_segment[-1]
                # 4. Złożenie ramki z powrotem
                result_data = (
                        header +
                        plain +
                        decrypted_segment +
                        data[-3:]  # FOOTER
                )

                return result_data, received_crc8 == calculated_crc8

            else:
                raise ValueError(f"Nieznana flaga protokołu: {flags}")

        except Exception as e:
            raise ValueError(f"Błąd podczas przetwarzania danych: {str(e)}")

    # ----wstawione dane koniec
    @staticmethod
    def extract_command_id(data: bytes) -> int:
        """
        Wydobywa COMMAND_ID z sekcji JAWNA
        """
        # COMMAND_ID znajduje się po DEVICE_ID (10B) w sekcji JAWNA
        command_id_start = 4 + 10  # HEADER(4B) + DEVICE_ID(10B)
        return int.from_bytes(data[command_id_start:command_id_start + 2], 'big')

    @staticmethod
    def parse_measure_data(data: bytes) -> MeasureDataPayload:
        """
        Parsuje dane dla komendy MEASURE_DATA (0x0003)
        """
        # Początek sekcji SZYFROWANA
        data_start = 4 + 17  # HEADER(4B) + JAWNA(17B)

        # Pomijamy DATA_LEN (1B)
        data_content_start = data_start + 1

        # Parsowanie pól
        status = data[data_content_start]
        request = data[data_content_start + 1]

        # Wydobycie pozostałych pól
        device_id = data[4:14].decode('ascii').strip()  # Wydobycie DEVICE_ID z sekcji JAWNA
        speed = data[data_content_start + 2:data_content_start + 8].decode('ascii').strip()
        rate = data[data_content_start + 8:data_content_start + 15].decode('ascii').strip()
        total = data[data_content_start + 15:data_content_start + 27].decode('ascii').strip()
        current_time = data[data_content_start + 27:data_content_start + 46].decode('ascii').strip()

        return MeasureDataPayload(
            deviceId=device_id,
            status=status,
            request=request,
            speed=speed,
            rate=rate,
            total=total,
            currentTime=current_time
        )

    @staticmethod
    def parse_alias_data(data: bytes) -> AliasDataPayload:
        """
        Parsuje dane dla komendy ALIAS_DATA (0x0002)
        """
        # Początek sekcji SZYFROWANA
        data_start = 4 + 17  # HEADER(4B) + JAWNA(17B)

        # Pomijamy DATA_LEN (1B)
        data_content_start = data_start + 1

        # Parsowanie pól
        status = data[data_content_start]
        request = data[data_content_start + 1]

        # Wydobycie pozostałych pól

        device_id = data[4:14].decode('ascii').strip()  # Wydobycie DEVICE_ID z sekcji JAWNA
        company = data[data_content_start + 2:data_content_start + 12].decode('ascii').strip()
        location = data[data_content_start + 12:data_content_start + 22].decode('ascii').strip()
        productName = data[data_content_start + 22:data_content_start + 32].decode('ascii').strip()
        scaleId = data[data_content_start + 32:data_content_start + 42].decode('ascii').strip()

        return AliasDataPayload(

           deviceId=device_id,
           company=company,
           location=location,
           productName=productName,
           scaleId=scaleId

        )

    @staticmethod
    def parse_dynamic_data(data: bytes) -> None:
        """
                Parsuje dane dla komendy DYNAMIC_DATA (0x0004)  i zapisuje w globalnym kontenerze

                """
        # Początek sekcji SZYFROWANA
        data_start = 4 + 17  # HEADER(4B) + JAWNA(17B)

        # Pomijamy DATA_LEN (1B)
        data_content_start = data_start + 1

        # Parsowanie pól
        status = data[data_content_start]
        request = data[data_content_start + 1]

        # Wydobycie DEVICE_ID z sekcji JAWNA
        device_id = data[4:14].decode('ascii').strip()

        # Wydobycie pozostałych pól
        mv_reading = data[data_content_start + 2:data_content_start + 10].decode('ascii').strip()
        conv_digits = data[data_content_start + 10:data_content_start + 18].decode('ascii').strip()
        scale_weight = data[data_content_start + 18:data_content_start + 26].decode('ascii').strip()
        belt_weight = data[data_content_start + 26:data_content_start + 34].decode('ascii').strip()
        current_time = data[data_content_start + 34:data_content_start + 53].decode('ascii').strip()

        # Zapisz odczyty w globalnym kontenerze
        dynamic_readings_store.update_readings(
            device_id=device_id,
            mv_reading=mv_reading,
            conv_digits=conv_digits,
            scale_weight=scale_weight,
            belt_weight=belt_weight,
            current_time=current_time
        )

        logger.info(f"Przechwycono odczyty dynamiczne - Reading:{mv_reading}, Digits:{conv_digits}, "
                    f"Scale:{scale_weight}, Belt:{belt_weight}, Time:{current_time}")



    #---------NOWY
    @staticmethod
    def parse_static_data(data: bytes) -> StaticDataPayload:
        """
        Parsuje dane dla komendy ALIAS_DATA (0x0002)
        """
        # Początek sekcji SZYFROWANA
        data_start = 4 + 17  # HEADER(4B) + JAWNA(17B)

        # Pomijamy DATA_LEN (1B)
        data_content_start = data_start + 1

        # Parsowanie pól
        status = data[data_content_start]
        request = data[data_content_start + 1]

        # Wydobycie pozostałych pól

        device_id = data[4:14].decode('ascii').strip()  # Wydobycie DEVICE_ID z sekcji JAWNA
        filterRate = data[data_content_start + 2:data_content_start + 3].decode('ascii').strip()
        scalecapacity = data[data_content_start +3:data_content_start + 11].decode('ascii').strip()
        autozero = data[data_content_start + 11:data_content_start + 19].decode('ascii').strip()
        deadband = data[data_content_start + 19:data_content_start + 27].decode('ascii').strip()
        scaletype = data[data_content_start + 27:data_content_start + 28].decode('ascii').strip()
        loadcellset = data[data_content_start + 28:data_content_start + 29].decode('ascii').strip()
        loadcellcapacity = data[data_content_start + 29:data_content_start + 37].decode('ascii').strip()
        trimm = data[data_content_start + 37:data_content_start + 45].decode('ascii').strip()
        idlerspacing = data[data_content_start + 45:data_content_start + 53].decode('ascii').strip()
        speedsource = data[data_content_start + 53:data_content_start + 54].decode('ascii').strip()
        wheeldiameter = data[data_content_start + 54:data_content_start + 62].decode('ascii').strip()
        pulsesperrev = data[data_content_start + 62:data_content_start + 69].decode('ascii').strip()
        beltlength = data[data_content_start + 69:data_content_start + 77].decode('ascii').strip()
        beltlengthpulses = data[data_content_start + 77:data_content_start + 85].decode('ascii').strip()
        currenttime = data[data_content_start + 85:data_content_start + 104].decode('ascii').strip()



        return StaticDataPayload(

            deviceId=device_id,
            filterRate=filterRate,
            scaleCapacity=scalecapacity,
            autoZero=autozero,
            deadBand=deadband,
            scaleType=scaletype,
            loadcellSet=loadcellset,
            loadcellCapacity=loadcellcapacity,
            trimm=trimm,
            idlerSpacing=idlerspacing,
            speedSource=speedsource,
            wheelDiameter=wheeldiameter,
            pulsesPerRev=pulsesperrev,
            beltLength=beltlength,
            beltLengthPulses=beltlengthpulses,
            currentTime=currenttime

        )
    #---------KONIEC NOWY
    @staticmethod
    def calculate_crc16(data: bytes) -> int:
        """
        Oblicza CRC16 dla danych
        """
        calculator = Calculator(CRC16_CCITT_CONFIG)
        return calculator.checksum(data)

        # crc = 0xFFFF
        # for byte in data:
        #     crc ^= byte
        #     for _ in range(8):
        #         if crc & 0x0001:
        #             crc = (crc >> 1) ^ 0xA001
        #         else:
        #             crc >>= 1
        # return crc

    @staticmethod
    def calculate_crc8(data: bytes) -> int:

        return sum(data) & 0xFF

       # calculator = Calculator(BYTE_CHECKSUM_CONFIG)
       # return calculator.checksum(data)

        # crc = 0x00  # wartość początkowa
        # polynomial = 0x07  # wielomian CRC-8
        #
        # for byte in data:
        #     crc ^= byte
        #     for _ in range(8):
        #         if crc & 0x80:
        #             crc = (crc << 1) ^ polynomial
        #         else:
        #             crc <<= 1
        #     crc &= 0xFF
        #
        # return crc


def command_support(command_id: int,
                    decoded_data: bytes,
                    flag: int ,
                    key1: str,
                    key2: str,
                    db: Session = Depends(get_db)):



    if command_id == CommandID.MEASURE_DATA:

        measure_data = ProtocolAnalyzer.parse_measure_data(decoded_data)

        # Tworzenie nowego rekordu w bazie danych
        # device_id = decoded_data[4:14].decode('ascii').strip()  # Wydobycie DEVICE_ID z sekcji JAWNA
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

        # tutaj kondycjonuje ramke odpowiedzi
        # ++++++++++++++++++++++++++++++++++++++++++++++++++++
        # Pobieramy DEVICE_ID i COMMAND_ID z sekcji JAWNA
        _device_id = decoded_data[4:14]  # 10 bajtów
        _command_id = decoded_data[14:16]  # 2 bajty

        # Przygotowanie odpowiedzi dla komendy 0003
        # Konwersja z bytes na int
        command_id_value = int.from_bytes(_command_id, 'big')
        # Ustawienie najstarszego bitu
        command_id_value |= 0x8000
        # Konwersja z powrotem na bytes
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
        status = 0x01  # przykładowy status
        request = 0x00  # przykładowy request

        response_data.append(0x02)  # DATA_LEN (2 bajty danych)
        response_data.append(status)  # STATUS (1B)
        response_data.append(request)  # REQUEST (1B)

        # Obliczenie CRC8 dla sekcji SZYFROWANA
        crc8 = ProtocolAnalyzer.calculate_crc8(response_data[-4:])  # dla DATA_LEN + DATA
        response_data.append(crc8)
        encrypted_segment = response_data[21:]
        # jesli flaga encode = true koduje dane
        if (flag & 0x01):
            response_data[3]=1
            cipher = RC4KeyGenerator.create_cipher(key1,key2)
            encrypted = cipher.encrypt(encrypted_segment)
            response_data[21:] = encrypted


        # Obliczenie CRC16 dla całości (bez znacznika końca)
        crc16 = ProtocolAnalyzer.calculate_crc16(response_data)
        response_data.extend(crc16.to_bytes(2, 'big'))  # CRC16 (2B)

        # FOOTER - znacznik końca
        response_data.append(0x55)  # END_MARKER (1B)

        # ++++++++++++++++++++++++++++++++++++++++++++++++++++
        # koniec kondycjonowania ramki odpowiedzi
        return Response(content=bytes(response_data), media_type="application/octet-stream")

    else:
        # Zarezerwowane na przyszłe implementacje innych komend
        return {
            "command": f"CMD_{command_id:04x}",
            "status": "not_implemented"
        }
        # return {
        #     "command": "MEASURE_DATA",
        #     "data": measure_data
        # }

    # elif:
# ----wstawiam koniec