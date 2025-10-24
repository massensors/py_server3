from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, asc
from typing import List, Optional
from datetime import datetime, date, timedelta


from starlette import status

from repositories.database import get_db
from models.models import MeasureData
from pydantic import BaseModel
from services.selected_device_store import selected_device_store
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/measure-data",
    tags=["measure data"],
    responses={404: {"description": "Not found"}},
)


class MeasureDataResponse(BaseModel):
    id: int
    deviceId: str
    speed: str
    rate: str
    total: str
    currentTime: str
    incremental_sum: Optional[float] = None  # Nowe pole

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


class MeasureDataListResponse(BaseModel):
    data: List[MeasureDataResponse]
    total_count: int
    shown_count: int
    sampling_info: str
    period_info: str
    device_id: Optional[str] = None


class PeriodSummary(BaseModel):
    """Podsumowanie dla wybranego okresu"""
    period_info: str
    device_id: str
    total_records: int
    speed_avg: Optional[float] = None
    speed_min: Optional[float] = None
    speed_max: Optional[float] = None
    rate_avg: Optional[float] = None
    rate_min: Optional[float] = None
    rate_max: Optional[float] = None
    total_sum: Optional[float] = None
    first_measurement: Optional[str] = None
    last_measurement: Optional[str] = None


# Istniejące podstawowe endpointy pozostają bez zmian
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


# NOWE ENDPOINTY Z FILTROWANIEM I INTELIGENTNYM PRÓBKOWANIEM
def _calculate_incremental_values(measures):
    """
    Oblicza sumę przyrostową dla listy pomiarów.

    Args:
        measures: Lista pomiarów posortowana od najstarszego do najnowszego

    Returns:
        Lista pomiarów z dodanym polem incremental_sum
    """
    if not measures or len(measures) == 0:
        return measures

    # Konwertuj wartości total na float
    total_values = []
    for m in measures:
        try:
            total_val = float(m.total)
            total_values.append(total_val)
        except (ValueError, TypeError):
            total_values.append(None)

    # Oblicz sumy przyrostowe używając tej samej logiki co w raportach
    incremental_sums = []
    current_sum = 0.0

    # Pierwszy pomiar (najstarszy) ma sumę 0
    incremental_sums.append(0.0)

    # Dla każdego kolejnego pomiaru
    for i in range(1, len(total_values)):
        current_val = total_values[i]
        prev_val = total_values[i - 1]

        if current_val is not None and prev_val is not None:
            if current_val >= prev_val:
                # Wartość rosła - dodaj różnicę
                current_sum += (current_val - prev_val)
            else:
                # Wartość spadła - reset, nie dodawaj
                pass

        incremental_sums.append(current_sum)

    # Dodaj sumy przyrostowe do obiektów pomiarów
    result = []
    for i, measure in enumerate(measures):
        measure_dict = {
            'id': measure.id,
            'deviceId': measure.deviceId,
            'speed': measure.speed,
            'rate': measure.rate,
            'total': measure.total,
            'currentTime': measure.currentTime,
            'incremental_sum': round(incremental_sums[i], 2) if i < len(incremental_sums) else 0.0
        }
        result.append(measure_dict)

    return result

@router.get("/filtered/list", response_model=MeasureDataListResponse)
async def get_filtered_measures(
        device_id: Optional[str] = Query(None, description="ID urządzenia (opcjonalne)"),
        start_date: Optional[date] = Query(None, description="Data początkowa (YYYY-MM-DD)"),
        end_date: Optional[date] = Query(None, description="Data końcowa (YYYY-MM-DD)"),
        period_type: Optional[str] = Query(None,
                                           description="Typ okresu: current_month, previous_month, current_year, previous_year, custom"),
        max_results: int = Query(1000, ge=10, le=5000, description="Maksymalna liczba rekordów (10-5000)"),
        db: Session = Depends(get_db)


):
    """
    Pobierz przefiltrowane dane pomiarowe z inteligentnym próbkowaniem.

    System automatycznie dobiera rozdzielczość wyświetlania w zależności od:
    - Wybranego okresu (więcej danych = rzadsze próbkowanie)
    - Limitu maksymalnych wyników
    - Dostępnej liczby rekordów
    """
    try:
        # Bazowe zapytanie
        query = db.query(MeasureData)

        # Filtrowanie po urządzeniu
        if not device_id:
            device_id = selected_device_store.get_device_id()

        if device_id:
            query = query.filter(MeasureData.deviceId == device_id)
            logger.info(f"Filtrowanie danych dla urządzenia: {device_id}")

        # Obsługa okresów z automatycznym obliczaniem dat
        calculated_start, calculated_end, period_display = _calculate_period_dates(period_type, start_date, end_date)

        # Filtrowanie po datach
        if calculated_start:
            start_str = calculated_start.strftime('%Y-%m-%d %H:%M:%S')
            query = query.filter(MeasureData.currentTime >= start_str)

        if calculated_end:
            end_str = calculated_end.strftime('%Y-%m-%d %H:%M:%S')
            query = query.filter(MeasureData.currentTime <= end_str)

        # Policz całkowitą liczbę rekordów
        total_count = query.count()

        if total_count == 0:
            return MeasureDataListResponse(
                data=[],
                total_count=0,
                shown_count=0,
                sampling_info="Brak danych dla wybranych kryteriów",
                period_info=period_display or "Wszystkie",
                device_id=device_id
            )

        # Inteligentne próbkowanie
        sampling_info, final_query = _apply_intelligent_sampling(
            query, total_count, max_results, calculated_start, calculated_end, db
        )

        # Pobierz przefiltrowane dane - SORTUJ OD NAJSTARSZEGO
        measures = final_query.all()

        # Posortuj w Pythonie od najstarszego do najnowszego
        measures.sort(key=lambda m: m.currentTime)

        # Oblicz sumy przyrostowe
        measures_with_incremental = _calculate_incremental_values(measures)

        # Odwróć kolejność dla wyświetlenia (najnowsze na górze)
        measures_with_incremental.reverse()

        # Konwersja na modele odpowiedzi
        measure_responses = [
            MeasureDataResponse(**m) for m in measures_with_incremental
        ]

        logger.info(f"Zwrócono {len(measure_responses)} z {total_count} dostępnych rekordów")

        return MeasureDataListResponse(
            data=measure_responses,
            total_count=total_count,
            shown_count=len(measure_responses),
            sampling_info=sampling_info,
            period_info=period_display or "Wszystkie",
            device_id=device_id
        )

    except Exception as e:
        logger.error(f"Błąd podczas filtrowania danych: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas filtrowania danych: {str(e)}"
        )


@router.get("/filtered/summary", response_model=PeriodSummary)
async def get_period_summary(
        device_id: Optional[str] = Query(None, description="ID urządzenia (opcjonalne)"),
        start_date: Optional[date] = Query(None, description="Data początkowa (YYYY-MM-DD)"),
        end_date: Optional[date] = Query(None, description="Data końcowa (YYYY-MM-DD)"),
        period_type: Optional[str] = Query(None, description="Typ okresu"),
        db: Session = Depends(get_db)
):
    """
    Pobierz podsumowanie statystyczne dla wybranego okresu.
    """
    try:
        if not device_id:
            device_id = selected_device_store.get_device_id()

        if not device_id:
            raise HTTPException(
                status_code=400,
                detail="Nie wybrano urządzenia"
            )

        # Oblicz daty okresu
        calculated_start, calculated_end, period_display = _calculate_period_dates(period_type, start_date, end_date)

        # Bazowe zapytanie z agregacjami
        query = db.query(
            func.count(MeasureData.id).label('total_records'),
            func.min(MeasureData.currentTime).label('first_measurement'),
            func.max(MeasureData.currentTime).label('last_measurement')
        ).filter(MeasureData.deviceId == device_id)

        # Dodatkowo sprawdź czy kolumny można konwertować na float
        numeric_query = db.query(
            func.avg(func.cast(MeasureData.speed, db.bind.dialect.NUMERIC)).label('speed_avg'),
            func.min(func.cast(MeasureData.speed, db.bind.dialect.NUMERIC)).label('speed_min'),
            func.max(func.cast(MeasureData.speed, db.bind.dialect.NUMERIC)).label('speed_max'),
            func.avg(func.cast(MeasureData.rate, db.bind.dialect.NUMERIC)).label('rate_avg'),
            func.min(func.cast(MeasureData.rate, db.bind.dialect.NUMERIC)).label('rate_min'),
            func.max(func.cast(MeasureData.rate, db.bind.dialect.NUMERIC)).label('rate_max'),
            func.sum(func.cast(MeasureData.total, db.bind.dialect.NUMERIC)).label('total_sum')
        ).filter(MeasureData.deviceId == device_id)

        # Filtrowanie po datach
        if calculated_start:
            start_str = calculated_start.strftime('%Y-%m-%d %H:%M:%S')
            query = query.filter(MeasureData.currentTime >= start_str)
            numeric_query = numeric_query.filter(MeasureData.currentTime >= start_str)

        if calculated_end:
            end_str = calculated_end.strftime('%Y-%m-%d %H:%M:%S')
            query = query.filter(MeasureData.currentTime <= end_str)
            numeric_query = numeric_query.filter(MeasureData.currentTime <= end_str)

        # Wykonaj zapytania
        basic_result = query.first()
        numeric_result = numeric_query.first()

        if not basic_result or basic_result.total_records == 0:
            return PeriodSummary(
                period_info=period_display or "Brak danych",
                device_id=device_id,
                total_records=0
            )

        return PeriodSummary(
            period_info=period_display or "Wszystkie",
            device_id=device_id,
            total_records=basic_result.total_records,
            speed_avg=float(numeric_result.speed_avg) if numeric_result.speed_avg else None,
            speed_min=float(numeric_result.speed_min) if numeric_result.speed_min else None,
            speed_max=float(numeric_result.speed_max) if numeric_result.speed_max else None,
            rate_avg=float(numeric_result.rate_avg) if numeric_result.rate_avg else None,
            rate_min=float(numeric_result.rate_min) if numeric_result.rate_min else None,
            rate_max=float(numeric_result.rate_max) if numeric_result.rate_max else None,
            total_sum=float(numeric_result.total_sum) if numeric_result.total_sum else None,
            first_measurement=basic_result.first_measurement,
            last_measurement=basic_result.last_measurement
        )

    except Exception as e:
        logger.error(f"Błąd podczas generowania podsumowania: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas generowania podsumowania: {str(e)}"
        )


def _calculate_period_dates(period_type, start_date, end_date):
    """Oblicza daty okresu na podstawie typu okresu lub podanych dat"""
    calculated_start = None
    calculated_end = None
    period_display = None

    if period_type:
        now = datetime.now()

        if period_type == "current_month":
            calculated_start = datetime(now.year, now.month, 1)
            if now.month == 12:
                calculated_end = datetime(now.year + 1, 1, 1) - timedelta(seconds=1)
            else:
                calculated_end = datetime(now.year, now.month + 1, 1) - timedelta(seconds=1)
            period_display = f"Bieżący miesiąc ({calculated_start.strftime('%Y-%m-%d')} - {calculated_end.strftime('%Y-%m-%d')})"

        elif period_type == "previous_month":
            if now.month == 1:
                calculated_start = datetime(now.year - 1, 12, 1)
                calculated_end = datetime(now.year, 1, 1) - timedelta(seconds=1)
            else:
                calculated_start = datetime(now.year, now.month - 1, 1)
                calculated_end = datetime(now.year, now.month, 1) - timedelta(seconds=1)
            period_display = f"Poprzedni miesiąc ({calculated_start.strftime('%Y-%m-%d')} - {calculated_end.strftime('%Y-%m-%d')})"

        elif period_type == "current_year":
            calculated_start = datetime(now.year, 1, 1)
            calculated_end = datetime(now.year, 12, 31, 23, 59, 59)
            period_display = f"Bieżący rok ({now.year})"

        elif period_type == "previous_year":
            calculated_start = datetime(now.year - 1, 1, 1)
            calculated_end = datetime(now.year - 1, 12, 31, 23, 59, 59)
            period_display = f"Poprzedni rok ({now.year - 1})"

        elif period_type == "custom":
            if start_date and end_date:
                calculated_start = datetime.combine(start_date, datetime.min.time())
                calculated_end = datetime.combine(end_date, datetime.max.time())
                period_display = f"Okres niestandardowy ({start_date} - {end_date})"

    # Zastąp obliczonymi datami jeśli podano własne
    if start_date and not period_type:
        calculated_start = datetime.combine(start_date, datetime.min.time())
    if end_date and not period_type:
        calculated_end = datetime.combine(end_date, datetime.max.time())

    if start_date and end_date and not period_type:
        period_display = f"Własny okres ({start_date} - {end_date})"

    return calculated_start, calculated_end, period_display


def _apply_intelligent_sampling(query, total_count, max_results, start_date, end_date, db):
    """Zastosuj inteligentne próbkowanie danych z całego zakresu czasowego"""

    if total_count <= max_results:
        # Mało danych - pokaż wszystko chronologicznie
        return "Wszystkie dostępne rekordy", query

    # Oblicz krok próbkowania aby równomiernie rozłożyć rekordy
    step = total_count / max_results

    # Pobierz WSZYSTKIE ID posortowane chronologicznie
    all_ids_query = query.with_entities(MeasureData.id).order_by(MeasureData.currentTime)
    all_ids = [row[0] for row in all_ids_query.all()]

    # Wybierz równomiernie rozłożone ID z całego zakresu
    sampled_ids = []
    for i in range(max_results):
        index = int(i * step)
        if index < len(all_ids):
            sampled_ids.append(all_ids[index])

    # Zawsze dołącz pierwszy i ostatni rekord
    if all_ids[0] not in sampled_ids:
        sampled_ids.insert(0, all_ids[0])
    if all_ids[-1] not in sampled_ids:
        sampled_ids.append(all_ids[-1])

    # Ogranicz do max_results
    if len(sampled_ids) > max_results:
        sampled_ids = sampled_ids[:max_results]

    # Oblicz rzeczywisty krok
    actual_step = total_count / len(sampled_ids)

    # Sprawdź czy faktycznie jest próbkowanie (pokazujemy mniej niż dostępne)
    if len(sampled_ids) >= total_count:
        sampling_info = f"Wszystkie rekordy ({total_count} dostępnych)"
    else:
        # Jest próbkowanie - pokaż szczegóły
        if actual_step >= 10:
            sampling_info = f"Próbkowanie: co ~{int(actual_step)} rekord z całego zakresu (wyświetlono {len(sampled_ids)} z {total_count})"
        elif actual_step >= 5:
            sampling_info = f"Próbkowanie: co ~{actual_step:.1f} rekord (wyświetlono {len(sampled_ids)} z {total_count})"
        else:
            sampling_info = f"Równomierne próbkowanie: co ~{actual_step:.2f} rekord (wyświetlono {len(sampled_ids)} z {total_count})"

    # Zwróć zapytanie z wybranymi ID
    sampled_query = query.filter(MeasureData.id.in_(sampled_ids))

    return sampling_info, sampled_query


@router.get("/count")
async def get_measures_count(
        device_id: Optional[str] = Query(None, description="ID urządzenia"),
        start_date: Optional[date] = Query(None, description="Data początkowa"),
        end_date: Optional[date] = Query(None, description="Data końcowa"),
        db: Session = Depends(get_db)
):
    """Szybkie sprawdzenie liczby rekordów"""
    try:
        query = db.query(func.count(MeasureData.id))

        if not device_id:
            device_id = selected_device_store.get_device_id()

        if device_id:
            query = query.filter(MeasureData.deviceId == device_id)

        if start_date:
            start_str = datetime.combine(start_date, datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S')
            query = query.filter(MeasureData.currentTime >= start_str)

        if end_date:
            end_str = datetime.combine(end_date, datetime.max.time()).strftime('%Y-%m-%d %H:%M:%S')
            query = query.filter(MeasureData.currentTime <= end_str)

        count = query.scalar()
        return {"count": count, "device_id": device_id}

    except Exception as e:
        logger.error(f"Błąd podczas liczenia rekordów: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Błąd podczas liczenia rekordów: {str(e)}"
        )