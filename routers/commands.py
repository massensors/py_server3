from enum import IntEnum
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
import struct
from Crypto.Cipher import ARC4
import hashlib


router = APIRouter(
    prefix="/commands",
    tags=["commands"],
    responses={404: {"description": "Not found"}}
)



class CommandID(IntEnum):
    """
    Dostępne komendy protokołu
    """
    CMD_0 = 0x0000
    CMD_1 = 0x0001
    CMD_2 = 0x0002
    MEASURE_DATA = 0x0003  # Komenda do przesyłania danych pomiarowych
    CMD_4 = 0x0004
    CMD_5 = 0x0005
    CMD_6 = 0x0006

class MeasureDataPayload(BaseModel):
    """
    Model danych dla komendy MEASURE_DATA (0x0003)
    """
    status: int
    request: int
    speed: str
    rate: str
    total: str
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
        
        return received_crc == calculated_crc
#---sha 256
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
#---sha 256 koniec
#----wstawione dane


    @staticmethod
    def encode_data(data: bytes, iterations: int, key1: str, key2: str ) -> tuple[bytes, bool]:
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
             footer = data[-3:]


             if len(encrypted_segment) < 2:  # Minimum to DATA_LEN(1B) + CRC8(1B)
                 raise ValueError("Segment SZYFROWANA jest zbyt krótki")

             # Pobranie długości danych i CRC8
             data_len = encrypted_segment[0]
             received_crc8 = encrypted_segment[-1]

             # Wyodrębnienie właściwych danych
             actual_data = encrypted_segment[1:-1]

             if  (flags & 0x01) == 0:  #IntegratorProtocol.ProtocolFlags.PLAIN.value:
                  # Dla danych niezaszyfrowanych tylko weryfikujemy CRC8
                data_to_check = bytes([data_len]) + actual_data
                calculated_crc8 = ProtocolAnalyzer.calculate_crc8(encrypted_segment[0:-1])
                return data, received_crc8 == calculated_crc8

             elif (flags & 0x01) == 1:  # IntegratorProtocol.ProtocolFlags.ENCRYPTED.value:
                  # Dla danych zaszyfrowanych
                  # 1. Inicjalizacja RC4
                  key = ProtocolAnalyzer._calculate_key(key1, key2, iterations)
                  cipher = ARC4.new(key)

                  # 2. Odszyfrowanie zakodowanej czesci z danymi
                  decrypted_segment = cipher.decrypt(encrypted_segment)

                  # 3. Weryfikacja CRC8
                  #data_to_check = bytes([data_len]) + decrypted_data
                  calculated_crc8 = ProtocolAnalyzer.calculate_crc8(decrypted_segment[0:-1])
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


#----wstawione dane koniec
    @staticmethod
    def extract_command_id(data: bytes) -> int:
        """
        Wydobywa COMMAND_ID z sekcji JAWNA
        """
        # COMMAND_ID znajduje się po DEVICE_ID (10B) w sekcji JAWNA
        command_id_start = 4 + 10  # HEADER(4B) + DEVICE_ID(10B)
        return int.from_bytes(data[command_id_start:command_id_start+2], 'big')

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
        speed = data[data_content_start+2:data_content_start+8].decode('ascii').strip()
        rate = data[data_content_start+8:data_content_start+15].decode('ascii').strip()
        total = data[data_content_start+15:data_content_start+27].decode('ascii').strip()
        current_time = data[data_content_start+27:data_content_start+46].decode('ascii').strip()
        
        return MeasureDataPayload(
            status=status,
            request=request,
            speed=speed,
            rate=rate,
            total=total,
            currentTime=current_time
        )
        
    @staticmethod
    def calculate_crc16(data: bytes) -> int:
        """
        Oblicza CRC16 dla danych
        """
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc

    @staticmethod
    def calculate_crc8(data: bytes) -> int:
        """
        Oblicza sumę kontrolną CRC8 dla DATA_LEN i DATA
        """
        crc = 0x00  # wartość początkowa
        polynomial = 0x07  # wielomian CRC-8

        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ polynomial
                else:
                    crc <<= 1
            crc &= 0xFF

        return crc



@router.post("/analyze")
async def analyze_data(data: bytes = Body(...)):
    """
    Endpoint do analizy przychodzącego strumienia danych
    """
    try:
        
        # Sprawdzenie poprawności ramki
        if not ProtocolAnalyzer.validate_frame(data):
            raise HTTPException(
                status_code=400,
                detail="Nieprawidłowa ramka: błąd znacznika końca lub sumy kontrolnej"
            )
        # teraz nalezy sprawdzic czy dane sa zakodowane
        decoded_data, crc_valid = ProtocolAnalyzer.encode_data(data,1000, "Massensors", "key2")

        # Sprawdzenie czy suma kontrolna jest poprawna
        if not crc_valid:
            raise HTTPException(
                status_code=400,
                detail="Nieprawidłowa suma kontrolna CRC8"
            )
        # Pobranie COMMAND_ID
        command_id = ProtocolAnalyzer.extract_command_id(decoded_data)
        
        # Obsługa różnych komend
        if command_id == CommandID.MEASURE_DATA:
            measure_data = ProtocolAnalyzer.parse_measure_data(decoded_data)
            return {
                "command": "MEASURE_DATA",
                "data": measure_data
            }
        else:
            # Zarezerwowane na przyszłe implementacje innych komend
            return {
                "command": f"CMD_{command_id:04x}",
                "status": "not_implemented"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Błąd przetwarzania danych: {str(e)}"
        )