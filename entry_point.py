import uvicorn
import os
import sys
import multiprocessing
from main import app

# To jest potrzebne dla PyInstaller na Windows przy wielowątkowości
multiprocessing.freeze_support()

if __name__ == "__main__":
    # POPRAWKA DLA --noconsole:
    # Jeśli aplikacja nie ma konsoli (sys.stdout jest None),
    # przekierowujemy wyjście do "nicości" (devnull), aby Uvicorn się nie wywalał.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")

    # Pobieramy port z ENV lub domyślnie 8080
    port = int(os.getenv("PORT", 8080))

    # Uruchamiamy serwer
    # workers=1 jest bezpieczniejsze dla wersji .exe,
    # chyba że bardzo potrzebujesz wydajności (wtedy wymaga testów)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info", workers=1)