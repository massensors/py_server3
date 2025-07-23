from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from starlette import status

from repositories.database import get_db
from models.models import MeasureData
from pydantic import BaseModel

router = APIRouter(
    prefix="/measure-data",
    tags=["measure data"],
    responses={404: {"description": "Not found"}},
)

class MeasureDataResponse(BaseModel):
    deviceId: str
    speed: str
    rate: str
    total: str
    currentTime: str

    class Config:
        from_attributes = True

class MeasureDataRequest(BaseModel):
    deviceId: str
    speed: str
    rate: str
    total: str
    currentTime: str

    class Config:
        json_schema_extra = {
            "example": {
                "deviceId": "BM #1",
                "speed": "0.86",
                "rate": "123.64",
                "total": "31560",
                "currentTime": "2023-01-01 00:00:00"
            }
        }

@router.get("/", response_model=List[MeasureDataResponse])
async def read_all_measures(db: Session = Depends(get_db)):
    """Pobierz wszystkie zadania"""
    return db.query(MeasureData).all()


@router.get("/{device_id}", response_model=MeasureDataResponse)
async def read_device_measures(device_id: str, db: Session = Depends(get_db)):
    """Pobierz zadanie po ID"""
    measures = db.query(MeasureData).filter(MeasureData.deviceId == device_id).first()
    if not measures:
        raise HTTPException(status_code=404, detail="Dane nie znalezione")
    return measures

@router.get("/device/{device_id}", response_model=List[MeasureDataResponse])
async def read_all_device_measures(device_id: str, db: Session = Depends(get_db)):
    """Pobierz wszystkie zadania dla danego urządzenia"""
    measures = db.query(MeasureData).filter(MeasureData.deviceId == device_id).all()
    if not measures:
        return []
    return measures


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_data_record(data_request: MeasureDataRequest, db: Session = Depends(get_db)):
    """Utwórz nowe zadanie"""
    data_model = MeasureData(**data_request.model_dump())
    db.add(data_model)
    db.commit()
    return {"status": "success", "message": "Zadanie utworzone"}