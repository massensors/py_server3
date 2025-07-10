from models.models import MeasureData
from fastapi.responses import Response
from routers.commands import CommandID, ProtocolAnalyzer
from fastapi import APIRouter, HTTPException, Body, Depends
from sqlalchemy.orm import Session
from repositories.database import get_db

def command_support(command_id: int, decoded_data: bytes, db: Session = Depends(get_db)):



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
        status = 0x00  # przykładowy status
        request = 0x01  # przykładowy request

        response_data.append(0x02)  # DATA_LEN (2 bajty danych)
        response_data.append(status)  # STATUS (1B)
        response_data.append(request)  # REQUEST (1B)

        # Obliczenie CRC8 dla sekcji SZYFROWANA
        crc8 = ProtocolAnalyzer.calculate_crc8(response_data[-4:])  # dla DATA_LEN + DATA
        response_data.append(crc8)

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