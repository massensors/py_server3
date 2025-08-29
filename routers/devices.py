import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, distinct
from typing import List, Dict, Optional
from starlette import status

from repositories.database import get_db
from models.models import Aliases
from pydantic import BaseModel
from sqlalchemy import func

# Konfiguracja loggera
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/devices",
    tags=["devices"],
    responses={404: {"description": "Not found"}},
)


class DeviceAliases(BaseModel):
    """Model dla aliasów urządzenia"""
    company: Optional[str] = None
    location: Optional[str] = None
    productName: Optional[str] = None
    scaleId: Optional[str] = None

    class Config:
        from_attributes = True


class DeviceInfo(BaseModel):
    """Model dla informacji o urządzeniu"""
    device_id: str
    aliases: DeviceAliases

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "145267893",
                "aliases": {
                    "company": "ACME Corp",
                    "location": "Magazyn A1",
                    "productName": "Waga przemysłowa",
                    "scaleId": "BM #3"
                }
            }
        }


class DevicesListResponse(BaseModel):
    """Model dla odpowiedzi listy urządzeń"""
    devices: List[DeviceInfo]
    count: int

    class Config:
        json_schema_extra = {
            "example": {
                "devices": [
                    {
                        "device_id": "145267893",
                        "aliases": {
                            "company": "ACME Corp",
                            "location": "Magazyn A1",
                            "productName": "Waga przemysłowa",
                            "scaleId": "BM #3"
                        }
                    }
                ],
                "count": 1
            }
        }


@router.get("/list", response_model=List[DeviceInfo])
async def get_devices_list(db: Session = Depends(get_db)):
    """
    Pobierz listę wszystkich urządzeń z ich najnowszymi aliasami.

    Zwraca listę unikalnych urządzeń na podstawie device_id z tabeli Aliases.
    Każde urządzenie zawiera swoje ID oraz najnowsze powiązane aliasy.
    """
    try:
        # Najpierw pobierz wszystkie unikalne deviceId
        unique_device_ids = db.query(Aliases.deviceId).distinct().all()

        devices = []
        for (device_id,) in unique_device_ids:
            # Dla każdego deviceId pobierz najnowszy rekord (według najwyższego id)
            latest_alias = (
                db.query(Aliases)
                .filter(Aliases.deviceId == device_id)
                .order_by(Aliases.id.desc())
                .first()
            )

            if latest_alias:
                device_info = DeviceInfo(
                    device_id=latest_alias.deviceId,
                    aliases=DeviceAliases(
                        company=latest_alias.company,
                        location=latest_alias.location,
                        productName=latest_alias.productName,
                        scaleId=latest_alias.scaleId
                    )
                )
                devices.append(device_info)

        logger.info(f"Pobrano listę {len(devices)} urządzeń z najnowszymi aliasami")

        # Debug log - wypisz pierwsze kilka deviceId
        for i, device in enumerate(devices[:5]):
            logger.info(f"Device {i+1}: ID={device.device_id}, company={device.aliases.company}")

        return devices

    except Exception as e:
        logger.error(f"Błąd podczas pobierania listy urządzeń: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas pobierania listy urządzeń: {str(e)}"
        )

@router.get("/list/summary", response_model=DevicesListResponse)
async def get_devices_list_with_summary(db: Session = Depends(get_db)):
    """
    Pobierz listę urządzeń wraz z podsumowaniem (liczba urządzeń).

    Rozszerzona wersja endpoint'u /list która dodatkowo zwraca liczbę urządzeń.
    """
    try:
        devices = await get_devices_list(db)

        return DevicesListResponse(
            devices=devices,
            count=len(devices)
        )

    except Exception as e:
        logger.error(f"Błąd podczas pobierania podsumowania urządzeń: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas pobierania podsumowania urządzeń: {str(e)}"
        )


@router.get("/count")
async def get_devices_count(db: Session = Depends(get_db)) -> Dict[str, int]:
    """
    Pobierz tylko liczbę urządzeń w bazie danych.

    Szybki endpoint do sprawdzania liczby urządzeń bez pobierania pełnych danych.
    """
    try:
        query = select(distinct(Aliases.deviceId))
        result = db.execute(query)
        count = len(result.scalars().all())

        logger.info(f"Liczba urządzeń w bazie: {count}")
        return {"count": count}

    except Exception as e:
        logger.error(f"Błąd podczas pobierania liczby urządzeń: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas pobierania liczby urządzeń: {str(e)}"
        )


@router.get("/{device_id}", response_model=DeviceInfo)
async def get_device_info(device_id: str, db: Session = Depends(get_db)):
    """
    Pobierz informacje o konkretnym urządzeniu.

    Args:
        device_id: ID urządzenia do pobrania

    Returns:
        Informacje o urządzeniu wraz z aliasami
    """
    try:
        # Znajdź urządzenie po ID
        alias = db.query(Aliases).filter(Aliases.deviceId == device_id).first()

        if not alias:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Urządzenie o ID '{device_id}' nie zostało znalezione"
            )

        device_info = DeviceInfo(
            device_id=alias.deviceId,
            aliases=DeviceAliases(
                company=alias.company,
                location=alias.location,
                productName=alias.productName,
                scaleId=alias.scaleId
            )
        )

        logger.info(f"Pobrano informacje o urządzeniu: {device_id}")
        return device_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Błąd podczas pobierania urządzenia {device_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas pobierania urządzenia: {str(e)}"
        )
@router.get("/search/by-alias")
async def search_devices_by_alias(
        company: Optional[str] = None,
        location: Optional[str] = None,
        product_name: Optional[str] = None,
        scale_id: Optional[str] = None,
        db: Session = Depends(get_db)
) -> List[DeviceInfo]:
    """
    Wyszukaj urządzenia po najnowszych aliasach.
    """
    try:
        # Pobierz wszystkie unikalne deviceId
        unique_device_ids = db.query(Aliases.deviceId).distinct().all()

        devices = []
        for (device_id,) in unique_device_ids:
            # Dla każdego deviceId pobierz najnowszy rekord
            latest_alias = (
                db.query(Aliases)
                .filter(Aliases.deviceId == device_id)
                .order_by(Aliases.id.desc())
                .first()
            )

            if latest_alias:
                # Sprawdź filtry wyszukiwania
                match = True

                if company and not (latest_alias.company and company.lower() in latest_alias.company.lower()):
                    match = False
                if location and not (latest_alias.location and location.lower() in latest_alias.location.lower()):
                    match = False
                if product_name and not (latest_alias.productName and product_name.lower() in latest_alias.productName.lower()):
                    match = False
                if scale_id and not (latest_alias.scaleId and scale_id.lower() in latest_alias.scaleId.lower()):
                    match = False

                if match:
                    device_info = DeviceInfo(
                        device_id=latest_alias.deviceId,
                        aliases=DeviceAliases(
                            company=latest_alias.company,
                            location=latest_alias.location,
                            productName=latest_alias.productName,
                            scaleId=latest_alias.scaleId
                        )
                    )
                    devices.append(device_info)

        logger.info(f"Znaleziono {len(devices)} urządzeń dla kryteriów wyszukiwania")
        return devices

    except Exception as e:
        logger.error(f"Błąd podczas wyszukiwania urządzeń: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas wyszukiwania urządzeń: {str(e)}"
        )