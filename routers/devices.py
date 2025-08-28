import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, distinct
from typing import List, Dict, Any, Optional
from starlette import status

from repositories.database import get_db
from models.models import Aliases
from pydantic import BaseModel

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
    Pobierz listę wszystkich urządzeń z ich aliasami.

    Zwraca listę unikalnych urządzeń na podstawie device_id z tabeli Aliases.
    Każde urządzenie zawiera swoje ID oraz powiązane aliasy.
    """
    try:
        # Pobranie wszystkich rekordów z tabeli Aliases
        # Grupujemy po deviceId żeby uniknąć duplikatów
        query = (
            select(Aliases)
            .distinct(Aliases.deviceId)
            .order_by(Aliases.deviceId)
        )

        result = db.execute(query)
        aliases_records = result.scalars().all()

        devices = []
        for record in aliases_records:
            device_info = DeviceInfo(
                device_id=record.deviceId,
                aliases=DeviceAliases(
                    company=record.company,
                    location=record.location,
                    productName=record.productName,
                    scaleId=record.scaleId
                )
            )
            devices.append(device_info)

        logger.info(f"Pobrano listę {len(devices)} urządzeń")
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
    Wyszukaj urządzenia po aliasach.

    Args:
        company: Nazwa firmy (częściowe dopasowanie)
        location: Lokalizacja (częściowe dopasowanie)
        product_name: Nazwa produktu (częściowe dopasowanie)
        scale_id: ID wagi (częściowe dopasowanie)

    Returns:
        Lista urządzeń spełniających kryteria wyszukiwania
    """
    try:
        query = db.query(Aliases)

        # Dodaj filtry jeśli parametry są podane
        if company:
            query = query.filter(Aliases.company.ilike(f"%{company}%"))
        if location:
            query = query.filter(Aliases.location.ilike(f"%{location}%"))
        if product_name:
            query = query.filter(Aliases.productName.ilike(f"%{product_name}%"))
        if scale_id:
            query = query.filter(Aliases.scaleId.ilike(f"%{scale_id}%"))

        results = query.all()

        devices = []
        for record in results:
            device_info = DeviceInfo(
                device_id=record.deviceId,
                aliases=DeviceAliases(
                    company=record.company,
                    location=record.location,
                    productName=record.productName,
                    scaleId=record.scaleId
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