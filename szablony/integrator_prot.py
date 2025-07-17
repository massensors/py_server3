from enum import Flag, auto
from dataclasses import dataclass
from typing import Optional, ClassVar
from pydantic import BaseModel
import struct

class IntegratorProtocol(BaseModel):
    """
    Pełna specyfikacja protokołu integratora
    
    Struktura ramki:
    +--------+---------+-------------+--------+
    | HEADER | JAWNA   | SZYFROWANA  | FOOTER |
    | (4B)   | (17B)   | (zmienna)   | (3B)   |
    +--------+---------+-------------+--------+
    """
    
    class ProtocolFlags(Flag):
        """
        Flagi protokołu (najniższy bit)
        """
        PLAIN = 0       # 0 - brak szyfrowania
        ENCRYPTED = 1   # 1 - dane zaszyfrowane RC4

    @dataclass
    class CipherConfig:
        """
        Konfiguracja szyfrowania RC4
        """
        DEFAULT_KEY: str = "KLUCZ"
        DEFAULT_ITERATIONS: int = 1000
    
    class FrameSegments:
        """
        Definicje wszystkich segmentów ramki
        """
        class Header:
            """
            Segment HEADER (4 bajty)
            """
            START_MARKER_1: bytes = b'\xAA'  # 1 bajt
            START_MARKER_2: bytes = b'\x55'  # 1 bajt
            VERSION: bytes                # 1 bajt
            FLAGS: bytes                  # 1 bajt
            
            TOTAL_SIZE: int = 4  # bytes
            
        class Plain:
            """
            Segment JAWNA (17 bajtów)
            Zawiera niezaszyfrowane informacje identyfikacyjne
            """
            DEVICE_ID: bytes    # 10 bajtów
            COMMAND_ID: bytes   # 2 bajty
            RC4_KEY_ID: bytes   # 1 bajt
            TIMESTAMP: bytes    # 3 bajty
            SEQ_NUM: bytes      # 1 bajt
            
            TOTAL_SIZE: int = 17  # bytes
            
        class Encrypted:
            """
            Segment SZYFROWANA (zmienna długość)
            Zawiera zaszyfrowane dane oraz informacje o ich długości
            """
            DATA_LEN: bytes    # 1 bajt - określa długość pola DATA
            DATA: bytes        # DATA_LEN bajtów
            CRC8: bytes       # 1 bajt - suma kontrolna dla DATA_LEN i DATA
            
            MIN_SIZE: int = 2  # bytes (DATA_LEN + CRC8, gdy brak danych)
            
        class Footer:
            """
            Segment FOOTER (3 bajty)
            Zawiera sumę kontrolną całej ramki i znacznik końca
            """
            CRC16: bytes      # 2 bajty - suma kontrolna dla HEADER + JAWNA + SZYFROWANA
            END_MARKER: bytes = b'\x55'  # 1 bajt
            
            TOTAL_SIZE: int = 3  # bytes

    class Validation:
        """
        Metody walidacji i obliczania sum kontrolnych
        """
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

        @staticmethod
        def calculate_crc16(data: bytes) -> int:
            """
            Oblicza sumę kontrolną CRC16 dla HEADER + JAWNA + SZYFROWANA
            """
            crc = 0xFFFF  # wartość początkowa
            polynomial = 0x1021  # wielomian CRC-16-CCITT
            
            for byte in data:
                crc ^= (byte << 8)
                for _ in range(8):
                    if crc & 0x8000:
                        crc = (crc << 1) ^ polynomial
                    else:
                        crc <<= 1
                crc &= 0xFFFF
            
            return crc

    class Parser:
        """
        Metody do parsowania i przetwarzania ramek
        """
        @staticmethod
        def validate_frame_markers(data: bytes) -> bool:
            """
            Sprawdza znaczniki początku i końca ramki
            """
            if len(data) < 7:  # minimum to HEADER(4B) + FOOTER(3B)
                return False
                
            return (data[0:2] == b'\xAA\x55' and 
                   data[-1:] == b'\x55')

        @staticmethod
        def is_encrypted(flags: int) -> bool:
            """
            Sprawdza czy segment SZYFROWANA jest zaszyfrowany
            """
            return bool(flags & IntegratorProtocol.ProtocolFlags.ENCRYPTED.value)

        @classmethod
        def decrypt_data(cls, data: bytes, key_id: int) -> bytes:
            """
            Deszyfruje dane używając RC4 z odpowiednim kluczem
            """
            # TODO: Implementacja deszyfrowania RC4
            pass

    class Builder:
        """
        Metody do budowania ramek
        """
        @staticmethod
        def create_frame(device_id: bytes, command_id: bytes, 
                        data: bytes, encrypt: bool = False) -> bytes:
            """
            Tworzy kompletną ramkę protokołu
            """
            # TODO: Implementacja tworzenia ramki
            pass

    # Stałe protokołu
    MIN_FRAME_SIZE: ClassVar[int] = (FrameSegments.Header.TOTAL_SIZE +
                                  FrameSegments.Plain.TOTAL_SIZE +
                                  FrameSegments.Encrypted.MIN_SIZE +
                                  FrameSegments.Footer.TOTAL_SIZE)  # 26 bajtów