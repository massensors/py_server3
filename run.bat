echo off
echo Uruchamianie serwera FastAPI...
cd /d "%~dp0"

REM Sprawdzenie czy istnieje srodowisko wirtualne
IF NOT EXIST ".venv\Scripts\python.exe" (
    echo BLAD: Nie znaleziono srodowiska wirtualnego w folderze .venv
    echo Upewnij sie, ze jestes w dobrym folderze.
    pause
    exit /b
)

REM Uruchomienie serwera
.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8080 --workers 4

echo Serwer zostal zatrzymany.
pause