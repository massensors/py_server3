import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from starlette import status

from repositories.database import get_db
from models.models import Aliases
from pydantic import BaseModel
from services.service_parameter_store import service_parameter_store


# Konfiguracja loggera
logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/aliases",
    tags=["aliases"],
    responses={404: {"description": "Not found"}},
)

class AliasesRequest(BaseModel):
    deviceId: str
    company: str
    location: str
    productName: str
    scaleId: str

    class Config:
        json_schema_extra = {
            "example": {
                "deviceId": "145267893",
                "company": "company",
                "location": "location",
                "productName": "product name",
                "scaleId": "BM #3"
            }
        }

class AliasesResponse(BaseModel):
    deviceId: str
    company: str
    location: str
    productName: str
    scaleId: str

    class Config:
        from_attributes = True


# Nowy model dla aktualizacji pojedynczego pola z adresem
class AliasFieldUpdate(BaseModel):
    field_address: int
    field_value: str

    class Config:
        json_schema_extra = {
            "example": {
                "field_address": 16,
                "field_value": "Nowa nazwa firmy"
            }
        }


# Mapowanie adresów na nazwy pól
ALIAS_ADDRESS_MAPPING = {
    16: 'company',
    17: 'location',
    18: 'productName',
    19: 'scaleId'
}


@router.get("/", response_model=List[AliasesResponse])
async def read_all_aliases(db:Session = Depends(get_db)):
    """Pobierz wszystkie aliasy"""
    return db.query(Aliases).all()



@router.get("/{device_id}", response_model=AliasesResponse)
async def read_device_aliases(device_id: str, db: Session = Depends(get_db)):
    """Pobierz pierwszy alias po ID urządzenia"""
    alias = db.query(Aliases).filter(Aliases.deviceId == device_id).first()
    if not alias:
        raise HTTPException(status_code=404, detail="Dane nie znalezione")
    return alias


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_data_record(data_request: AliasesRequest, db: Session = Depends(get_db)):
    """Utwórz nowy alias"""
    data_model = Aliases(**data_request.model_dump())
    db.add(data_model)
    db.commit()
    return {"status": "success", "message": "Alias utworzony"}


# Nowy endpoint do aktualizacji pojedynczego pola z adresem
@router.put("/{device_id}/field/{field_address}", status_code=status.HTTP_200_OK)
async def update_alias_field(device_id: str, field_address: int, field_update: AliasFieldUpdate,
                             db: Session = Depends(get_db)):
    """Aktualizuj pojedyncze pole aliasu dla określonego urządzenia używając adresu pola"""

    # Sprawdź czy adres jest prawidłowy
    if field_address not in ALIAS_ADDRESS_MAPPING:
        available_addresses = list(ALIAS_ADDRESS_MAPPING.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Nieprawidłowy adres pola. Dostępne adresy: {available_addresses}"
        )

    # Sprawdź czy adres w URL zgadza się z adresem w body
    if field_address != field_update.field_address:
        raise HTTPException(
            status_code=400,
            detail=f"Adres pola w URL ({field_address}) nie zgadza się z adresem w body ({field_update.field_address})"
        )

    # Pobierz nazwę pola na podstawie adresu
    field_name = ALIAS_ADDRESS_MAPPING[field_address]

    # Znajdź alias dla danego urządzenia
    alias = db.query(Aliases).filter(Aliases.deviceId == device_id).first()

    # ---------------------
    # NOWE: Zapisz parametry w store dla kontrolera
    service_parameter_store.store_parameters(device_id, field_address, field_update.field_value)
    logger.info(f"Parametry zapisane w store dla kontrolera: {device_id}, {field_address}, {field_update.field_value}")
    # ---------------------

    if not alias:
        # Jeśli alias nie istnieje, utwórz nowy z domyślnymi wartościami
        alias_data = {
            'deviceId': device_id,
            'company': '',
            'location': '',
            'productName': '',
            'scaleId': ''
        }
        # Ustaw wartość dla aktualizowanego pola
        alias_data[field_name] = field_update.field_value

        alias = Aliases(**alias_data)
        db.add(alias)
        db.commit()
        db.refresh(alias)


        return {
            "status": "success",
            "message": f"Utworzono nowy alias i zaktualizowano pole '{field_name}' (adres {field_address})",
            "field_address": field_address,
            "field_name": field_name,
            "old_value": "",
            "new_value": field_update.field_value
        }
    else:
        # Aktualizuj istniejący alias
        old_value = getattr(alias, field_name)
        setattr(alias, field_name, field_update.field_value)

        db.commit()
        db.refresh(alias)

        return {
            "status": "success",
            "message": f"Pole '{field_name}' (adres {field_address}) zostało zaktualizowane",
            "field_address": field_address,
            "field_name": field_name,
            "old_value": old_value,
            "new_value": field_update.field_value
        }
