from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import and_
from repositories.database import get_db
from models.models import MeasureData, Aliases
from services.selected_device_store import selected_device_store
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import csv
import io
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def safe_float_convert(value):
    """Bezpieczna konwersja na float"""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def calculate_incremental_sum(total_values):
    """
    Specjalny algorytm do obliczania sumy przyrostowej.
    Suma = suma różnic między pierwszym a ostatnim największym pomiarem w każdym segmencie.

    Args:
        total_values: Lista wartości total w kolejności chronologicznej

    Returns:
        Obliczona suma przyrostowa
    """
    if not total_values or len(total_values) < 2:
        return 0.0

    segments = []
    current_segment = [total_values[0]]

    # Podziel na segmenty - nowy segment gdy wartość spada
    for i in range(1, len(total_values)):
        current_val = total_values[i]
        prev_val = total_values[i-1]

        if current_val < prev_val:
            # Wartość spadła - zakończ obecny segment i zacznij nowy
            if len(current_segment) > 1:
                segments.append(current_segment)
            current_segment = [current_val]
        else:
            current_segment.append(current_val)

    # Dodaj ostatni segment
    if len(current_segment) > 1:
        segments.append(current_segment)

    # Oblicz sumę różnic w każdym segmencie
    incremental_sum = 0.0
    for segment in segments:
        if len(segment) >= 2:
            segment_diff = max(segment) - min(segment)
            incremental_sum += segment_diff
            logger.info(f"Segment: {segment} -> różnica: {segment_diff}")

    logger.info(f"Obliczona suma przyrostowa: {incremental_sum}")
    return incremental_sum


def parse_date_string(date_str):
    """
    Bezpieczne parsowanie daty z różnych formatów
    """
    if not date_str:
        return None

    # Lista formatów do sprawdzenia
    formats_to_try = [
        "%Y-%m-%d",  # ISO format (2024-08-01)
        "%Y-%m-%dT%H:%M:%S",  # ISO z czasem
        "%Y-%m-%dT%H:%M:%S.%f",  # ISO z mikrosekundami
    ]

    for fmt in formats_to_try:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    # Jeśli nic nie zadziałało, spróbuj z dateutil
    try:
        from dateutil import parser
        return parser.parse(date_str)
    except:
        raise ValueError(f"Nie można sparsować daty: {date_str}")


@router.get("/generate-report")
async def generate_report(
        period_type: str,
        start_date: str = None,
        end_date: str = None,
        db: Session = Depends(get_db)
):
    """
    Generuje raport CSV dla wybranego okresu i urządzenia.
    """
    try:
        # Pobierz aktualnie wybrane urządzenie
        current_selection = selected_device_store.get_device_id()
        if not current_selection:
            raise HTTPException(status_code=400, detail="Brak wybranego urządzenia")

        device_id = current_selection
        logger.info(f"Generowanie raportu dla urządzenia: {device_id}")

        # Oblicz zakres dat na podstawie period_type
        now = datetime.now()

        if period_type == "custom":
            if not start_date or not end_date:
                raise HTTPException(status_code=400, detail="Brak dat dla okresu niestandardowego")
                # ✅ POPRAWIONE: Użyj bezpiecznego parsowania
            try:
               date_from = parse_date_string(start_date)
               date_to = parse_date_string(end_date)
               logger.info(f"Sparsowane daty - od: {date_from}, do: {date_to}")
            except ValueError as e:
                logger.error(f"Błąd parsowania dat: {e}")
                raise HTTPException(status_code=400, detail=f"Nieprawidłowy format daty: {str(e)}")


        elif period_type == "current_month":
            date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            date_to = (date_from + relativedelta(months=1)) - timedelta(seconds=1)
        elif period_type == "previous_month":
            date_from = (now.replace(day=1) - relativedelta(months=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            date_to = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
        elif period_type == "current_year":
            date_from = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            date_to = now.replace(month=12, day=31, hour=23, minute=59, second=59)
        elif period_type == "previous_year":
            prev_year = now.year - 1
            date_from = datetime(prev_year, 1, 1, 0, 0, 0)
            date_to = datetime(prev_year, 12, 31, 23, 59, 59)
        else:
            raise HTTPException(status_code=400, detail="Nieprawidłowy typ okresu")

        logger.info(f"Zakres dat: {date_from} - {date_to}")

        # Pobierz dane pomiarowe
        measurements_query = db.query(MeasureData).filter(
            and_(
                MeasureData.deviceId == device_id,
                MeasureData.currentTime >= date_from,
                MeasureData.currentTime <= date_to
            )
        ).order_by(MeasureData.currentTime)

        measurements = measurements_query.all()

        if not measurements:
            raise HTTPException(status_code=404, detail="Brak danych pomiarowych dla wybranego okresu")

        # Pobierz aliasy urządzenia
        aliases = db.query(Aliases).filter(Aliases.deviceId == device_id).first()

        # ✅ POPRAWIONE: Konwertuj stringi na float z bezpieczną obsługą błędów
        speeds = []
        rates = []
        totals = []

        for m in measurements:
            speed_val = safe_float_convert(m.speed)
            if speed_val is not None:
                speeds.append(speed_val)

            rate_val = safe_float_convert(m.rate)
            if rate_val is not None:
                rates.append(rate_val)

            total_val = safe_float_convert(m.total)
            if total_val is not None:
                totals.append(total_val)

        logger.info(f"Konwertowane dane - speeds: {len(speeds)}, rates: {len(rates)}, totals: {len(totals)}")

        # Oblicz statystyki
        avg_speed = sum(speeds) / len(speeds) if speeds else 0
        max_speed = max(speeds) if speeds else 0
        avg_rate = sum(rates) / len(rates) if rates else 0
        max_rate = max(rates) if rates else 0

        # Oblicz sumę przyrostową używając specjalnego algorytmu
        incremental_sum = calculate_incremental_sum(totals)

        # Przygotuj dane do CSV
        csv_data = io.StringIO()
        writer = csv.writer(csv_data, delimiter=';')

        # Nagłówek raportu
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        period_str = f"{date_from.strftime('%Y-%m-%d')} - {date_to.strftime('%Y-%m-%d')}"

        writer.writerow(["RAPORT POMIAROWY"])
        writer.writerow(["Data raportu:", current_date])
        writer.writerow(["Okres:", period_str])
        writer.writerow(["ID urządzenia:", device_id])
        writer.writerow([])

        # Aliasy
        if aliases:
            writer.writerow(["ALIASY URZĄDZENIA:"])
            writer.writerow(["Firma:", aliases.company or ""])
            writer.writerow(["Lokalizacja:", aliases.location or ""])
            writer.writerow(["Nazwa produktu:", aliases.productName or ""])
            writer.writerow(["ID wagi:", aliases.scaleId or ""])
            writer.writerow([])

        # Statystyki
        writer.writerow(["STATYSTYKI:"])
        writer.writerow(["Średnia prędkość:", f"{avg_speed:.2f}"])
        writer.writerow(["Maksymalna prędkość:", f"{max_speed:.2f}"])
        writer.writerow(["Średnie natężenie:", f"{avg_rate:.2f}"])
        writer.writerow(["Maksymalne natężenie:", f"{max_rate:.2f}"])
        writer.writerow(["Suma przyrostowa:", f"{incremental_sum:.2f}"])
        writer.writerow(["Liczba pomiarów:", len(measurements)])
        writer.writerow([])

        # Dane szczegółowe
        writer.writerow(["SZCZEGÓŁOWE DANE POMIAROWE:"])
        writer.writerow(["Data i czas", "Prędkość", "Natężenie", "Suma"])

        for measurement in measurements:
            # ✅ POPRAWIONE: Konwersja przy wyświetlaniu
            speed_str = f"{safe_float_convert(measurement.speed):.2f}" if safe_float_convert(measurement.speed) is not None else ""
            rate_str = f"{safe_float_convert(measurement.rate):.2f}" if safe_float_convert(measurement.rate) is not None else ""
            total_str = f"{safe_float_convert(measurement.total):.2f}" if safe_float_convert(measurement.total) is not None else ""

            writer.writerow([
                measurement.currentTime,  # currentTime może być już string
                speed_str,
                rate_str,
                total_str
            ])

        # Przygotuj odpowiedź CSV
        csv_content = csv_data.getvalue()
        csv_data.close()

        # Nazwa pliku - bezpieczne nazewnictwo
        safe_device_id = str(device_id).replace(' ', '_').replace('/', '_')
        filename = f"raport_{safe_device_id}_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.csv"

        return Response(
            content=csv_content.encode('utf-8-sig'),  # BOM dla Excela
            media_type='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        logger.error(f"Błąd generowania raportu: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Błąd generowania raportu: {str(e)}")