@echo off
echo Budowanie wersji produkcyjnej (EXE)...

REM Aktywacja wirtualnego srodowiska (jesli nie jest aktywne)
call .venv\Scripts\activate

REM Instalacja PyInstaller (jesli nie masz)
pip install pyinstaller

REM Czyszczenie poprzednich budow
rmdir /s /q build
rmdir /s /q dist
del /f /q MeasurementSystem.spec

echo Tworzenie pliku EXE...
REM --onedir: tworzy folder (szybsze uruchamianie niz --onefile)
REM --name: nazwa pliku wyjsciowego
REM --hidden-import: wymuszamy dolaczenie sterownikow SQL i Uvicorn
REM --noconsole: ukrywa czarne okno (opcjonalne, dla serwera lepiej zostawic konsole do podgladu lub uzyc start_hiden.vbs)

pyinstaller --noconsole --onedir --name="MonitorBeltMate" ^
 --hidden-import=uvicorn.logging ^
 --hidden-import=uvicorn.loops ^
 --hidden-import=uvicorn.loops.auto ^
 --hidden-import=uvicorn.protocols ^
 --hidden-import=uvicorn.protocols.http ^
 --hidden-import=uvicorn.protocols.http.auto ^
 --hidden-import=uvicorn.lifespan ^
 --hidden-import=uvicorn.lifespan.on ^
 --hidden-import=sqlalchemy.sql.default_comparator ^
 --hidden-import=engineio.async_drivers.asgi ^
 entry_point.py

echo.
echo ---------------------------------------------------
echo Budowanie zakonczone!
echo Skopiuj folder 'frontend' oraz plik '.env' do folderu: dist\MonitorBeltMate\
echo ---------------------------------------------------
pause