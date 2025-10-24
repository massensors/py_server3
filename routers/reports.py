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





def format_number_for_csv(value, decimal_places=2):
    """
    Formatuje liczbę zmiennoprzecinkową dla CSV z przecinkiem jako separatorem dziesiętnym

    Args:
        value: Wartość do sformatowania (float lub None)
        decimal_places: Liczba miejsc po przecinku (domyślnie 2)

    Returns:
        String z liczbą używającą przecinka zamiast kropki, lub pusty string dla None
    """
    if value is None:
        return ""

    try:
        # Formatuj liczbę z określoną precyzją
        formatted = f"{float(value):.{decimal_places}f}"
        # Zamień kropkę na przecinek
        return formatted.replace('.', ',')
    except (ValueError, TypeError):
        return ""




def calculate_incremental_sum(total_values):
    """
    Specjalny algorytm do obliczania sumy przyrostowej.
    Suma = suma różnic między pierwszym a ostatnim największym pomiarem w każdym segmencie.

    Args:
        total_values: Lista wartości total w kolejności chronologicznej

    Returns:
        Obliczona suma przyrostowa
    """
    if not total_values:
        return 0.0

    if len(total_values) == 1:
        return 0.0

    segments = []
    current_segment = [total_values[0]]

    # Podziel na segmenty - nowy segment gdy wartość spada
    for i in range(1, len(total_values)):
        current_val = total_values[i]
        prev_val = total_values[i - 1]

        if current_val < prev_val:
            # Wartość spadła - zakończ obecny segment
            segments.append(current_segment)
            # Zacznij nowy segment z bieżącą wartością
            current_segment = [current_val]
        else:
            # Wartość rosnie lub się nie zmienia
            current_segment.append(current_val)

    # ZAWSZE dodaj ostatni segment (nawet jeśli ma 1 element)
    segments.append(current_segment)

    logger.info(f"Znaleziono {len(segments)} segmentów")

    # Oblicz sumę różnic w każdym segmencie
    incremental_sum = 0.0
    for idx, segment in enumerate(segments):
        if len(segment) >= 2:
            # Różnica między ostatnim a pierwszym (nie max-min!)
            segment_diff = segment[-1] - segment[0]
            incremental_sum += segment_diff
            logger.info(
                f"Segment {idx + 1}: [{segment[0]} ... {segment[-1]}] (długość: {len(segment)}) -> różnica: {segment_diff}")
        else:
            logger.info(f"Segment {idx + 1}: {segment} (długość: 1) -> pominięty")

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
            writer.writerow(["Średnia prędkość:", format_number_for_csv(avg_speed, 2)])
            writer.writerow(["Maksymalna prędkość:", format_number_for_csv(max_speed, 2)])
            writer.writerow(["Średnie natężenie:", format_number_for_csv(avg_rate, 2)])
            writer.writerow(["Maksymalne natężenie:", format_number_for_csv(max_rate, 2)])
            writer.writerow(["Suma przyrostowa:", format_number_for_csv(incremental_sum, 2)])
            writer.writerow(["Liczba pomiarów:", len(measurements)])
            writer.writerow([])

            # Dane szczegółowe
            writer.writerow(["SZCZEGÓŁOWE DANE POMIAROWE:"])
            writer.writerow(["Data i czas", "Prędkość", "Natężenie", "Suma", "Suma Przyrostowa"])

            # Oblicz sumy przyrostowe dla raportu
            cumulative_incremental = 0.0
            prev_total = None

            for measurement in measurements:
                # Konwersje wartości
                speed_str = format_number_for_csv(safe_float_convert(measurement.speed), 2)
                rate_str = format_number_for_csv(safe_float_convert(measurement.rate), 2)
                total_val = safe_float_convert(measurement.total)
                total_str = format_number_for_csv(total_val, 2)

                # Oblicz sumę przyrostową
                if prev_total is None:
                    # Pierwszy pomiar
                    incremental_str = format_number_for_csv(0.0, 2)
                else:
                    if total_val is not None and total_val >= prev_total:
                        cumulative_incremental += (total_val - prev_total)
                    incremental_str = format_number_for_csv(cumulative_incremental, 2)

                prev_total = total_val

                writer.writerow([
                    measurement.currentTime,  # currentTime może być już string
                    speed_str,
                    rate_str,
                    total_str,
                    incremental_str
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