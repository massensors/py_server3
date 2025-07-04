from enum import IntEnum
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
import struct

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

router = APIRouter(
    prefix="/integrator-prot",
    tags=["integrator protocol"],
    responses={404: {"description": "Not found"}}
)

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

        # jesli tak to nalezy je odkodowac zanim przejdziemy do nastepnego kroku
        # w odkodowanych danych nalezy sprawdzic sume kontrolna CRC8
        # jesli suma sie zgadza mozna dane validowac

        # Pobranie COMMAND_ID
        command_id = ProtocolAnalyzer.extract_command_id(data)
        
        # Obsługa różnych komend
        if command_id == CommandID.MEASURE_DATA:
            measure_data = ProtocolAnalyzer.parse_measure_data(data)
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