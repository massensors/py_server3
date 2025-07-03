from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from starlette import status

from database import get_db
from models import MeasureData, Aliases
from pydantic import BaseModel,fields




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


@router.get("/{device_id}", response_model=AliasesResponse)
async def read_device_aliases(device_id: str, db: Session = Depends(get_db)):
    """Pobierz aliasy po ID"""
    aliases = db.query(Aliases).filter(Aliases.deviceId == device_id).all()
    if not aliases:
        raise HTTPException(status_code=404, detail="Dane nie znalezione")
    return aliases

@router.get("/", response_model=List[AliasesResponse])
async def read_all_aliases(db:Session = Depends(get_db)):
    """Pobierz wszystkie aliasy"""
    return db.query(Aliases).all()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_data_record(data_request: AliasesRequest, db: Session = Depends(get_db)):
    """Utwórz nowe zadanie"""
    data_model = Aliases(**data_request.model_dump())
    db.add(data_model)
    db.commit()
    return {"status": "success", "message": "Zadanie utworzone"}




