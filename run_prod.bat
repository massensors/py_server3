
@echo off
echo Uruchamianie Systemu Pomiarowego...
cd /d "%~dp0"

REM Sprawdzenie czy plik exe istnieje
IF NOT EXIST "MonitorBeltMate.exe" (
    echo BLAD: Nie znaleziono pliku MonitorBeltMate.exe!
    pause
    exit /b
)

REM Uruchomienie aplikacji
REM Nie potrzebujemy Pythona, uruchamiamy bezposrednio exe
start "" "MonitorBeltMate.exe"

echo Aplikacja zostala uruchomiona w tle.
echo Otworz przegladarke na http://localhost:8080
REM Czekaj 3 sekundy
timeout /t 3 >nul