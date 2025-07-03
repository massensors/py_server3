from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from starlette import status

from database import get_db
from models import  StaticParams
from pydantic import BaseModel,fields




router = APIRouter(
    prefix="/static",
    tags=["static params"],
    responses={404: {"description": "Not found"}},
)

class StaticParamsResponse(BaseModel):
    deviceId: str
    filterRate: str
    scaleCapacity: str
    autoZero: str
    deadBand: str
    scaleType: str
    loadcellSet: str
    loadcellCapacity: str
    trimm: str
    idlerSpacing: str
    speedSource: str
    wheelDiameter: str
    pulsesPerRev: str
    beltLength: str
    beltLengthPulses: str
    currentTime: str

    class Config:
        from_attributes = True




class StaticParamsRequest(BaseModel):
    deviceId : str
    filterRate: str
    scaleCapacity : str
    autoZero  : str
    deadBand : str
    scaleType : str
    loadcellSet : str
    loadcellCapacity : str
    trimm : str
    idlerSpacing : str
    speedSource : str
    wheelDiameter : str
    pulsesPerRev : str
    beltLength : str
    beltLengthPulses : str
    currentTime : str

    class Config:
        json_schema_extra = {
            "example": {
                 "deviceId":"145267893",
                 "filterRate":"5",
                 "scaleCapacity":"150",
                 "autoZero"  : "0.7",
                 "deadBand" : "1.3",
                 "scaleType" : "1",
                 "loadcellSet" : "1",
                 "loadcellCapacity" : "150",
                 "trimm" : "10000",
                 "idlerSpacing" : "2.34",
                 "speedSource" : "1",
                 "wheelDiameter" : "20.0",
                 "pulsesPerRev" : "38",
                 "beltLength" : "25.5",
                 "beltLengthPulses" : "2240",
                 "currentTime" : "2023-01-01 00:00:00"
            }
        }

@router.get("/{device_id}", response_model=StaticParamsResponse)
async def read_device_params(device_id: str, db: Session = Depends(get_db)):
    """Pobierz parametry po ID"""
    params = db.query(StaticParams).filter(StaticParams.deviceId == device_id).all()
    if not params:
           raise HTTPException(status_code=404, detail="Dane nie znalezione")
    return params

@router.get("/", response_model=List[StaticParamsResponse])
async def read_all_params(db:Session = Depends(get_db)):
    """Pobierz wszystkie aliasy"""
    return db.query(StaticParams).all()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_data_record(data_request: StaticParamsRequest, db: Session = Depends(get_db)):
    """Utwórz nowe zadanie"""
    data_model = StaticParams(**data_request.model_dump())
    db.add(data_model)
    db.commit()
    return {"status": "success", "message": "Zadanie utworzone"}




