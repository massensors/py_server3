import logging
from fastapi import APIRouter, HTTPException, Body, Depends
from sqlalchemy.orm import Session
from repositories.database import get_db
from services.support import command_support, ProtocolAnalyzer
from fastapi.responses import Response


# Dodanie loggera
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/commands",
    tags=["commands"],
    responses={404: {"description": "Not found"}}
)



@router.post("/analyze")
async def analyze_data(data: bytes = Body(...), db: Session = Depends(get_db)):
    """
    Endpoint do analizy przychodzącego strumienia danych i zapisu do bazy
    """
    try:
        
        # Sprawdzenie poprawności ramki
        if not ProtocolAnalyzer.validate_frame(data):
            raise HTTPException(
                status_code=400,
                detail="Nieprawidłowa ramka: błąd znacznika końca lub sumy kontrolnej"
            )
        # teraz nalezy sprawdzic czy dane sa zakodowane
        decoded_data, crc_valid = ProtocolAnalyzer.encode_data(data,999, "Massensors", "Massensors")

        # Sprawdzenie czy suma kontrolna jest poprawna
        if not crc_valid:
            raise HTTPException(
                status_code=400,
                detail="Nieprawidłowa suma kontrolna CRC8"
            )

        #command_id = decoded_data[14:16]  # 2 bajty
        #device_id = decoded_data[4:14]  # 10 bajtów



        # Pobranie COMMAND_ID
        command_id = ProtocolAnalyzer.extract_command_id(decoded_data)
        # Obsługa różnych komend
        response = command_support(command_id, decoded_data, db)

        # Jeśli response jest już obiektem Response, zwróć go bezpośrednio
        if isinstance(response, Response):
            logger.debug(f"Zawartość ramki zwrotnej: {response.body.hex(' ')}")

            return response

        # W przeciwnym razie zwróć jako JSON
        logger.debug(f"Zawartość odpowiedzi JSON: {response}")
        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Błąd przetwarzania danych: {str(e)}"
        )