import logging
import  sys
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles  # Dodajemy import
from fastapi.responses import FileResponse  # Dodajemy import dla serwowania pliku HTML
from repositories.database import init_db
from routers import measure_data, aliases, static_params, commands, app_interface, dynamic_readings, devices, \
    network_observer
from routers.service_mode import router as service_mode_router
from routers import device_selection
from routers import measure_data
from routers import reports


import uvicorn

#commit push test 2



config = uvicorn.Config(
    "main:app",
    host="0.0.0.0",
    port=8080,
    log_level="debug",
    reload=True,
    log_config={
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(asctime)s - %(message)s",
                "use_colors": True,
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "": {"handlers": ["default"], "level": "DEBUG"},
        },
    },
)



# Usuń wszystkie handlery
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Nowa konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug.log', mode='w')
    ]
)

# Ustaw poziom logowania dla głównego loggera
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Na początku main.py, zaraz po konfiguracji loggera
logger.debug("Test loggera - DEBUG")
logger.info("Test loggera - INFO")
logger.warning("Test loggera - WARNING")
logger.error("Test loggera - ERROR")




# Inicjalizacja aplikacji FastAPI
app = FastAPI(title="System pomiarowy API")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    try:
        logger.debug("="*50)
        logger.debug(f"[REQUEST] Method: {request.method} Path: {request.url.path}")
        logger.debug(f"Headers: {dict(request.headers)}")
        body = await request.body()
        logger.debug(f"Request body: {body.hex(' ')}")
        response = await call_next(request)
        logger.debug(f"[RESPONSE] Status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Błąd w middleware: {str(e)}")
        raise




# Inicjalizacja bazy danych
init_db()

# Dodanie routerów

app.include_router(measure_data.router)
app.include_router(aliases.router)
app.include_router(static_params.router)

app.include_router(commands.router)

app.include_router(app_interface.router)  # Dodanie nowego routera dla aplikacji

app.include_router(service_mode_router)
app.include_router(dynamic_readings.router)  # NOWY ROUTER
app.include_router(devices.router)
app.include_router(device_selection.router)

app.include_router(network_observer.router)
app.include_router(reports.router, prefix="/reports", tags=["reports"])







# Dodanie obsługi plików statycznych
#app.mount("/static", StaticFiles(directory="static"), name="static")
#app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")  # DODANE!

# Endpoint zwracający główny plik HTML interfejsu
@app.get("/ui")
async def get_ui():
    #return FileResponse("static/index.html")
    return FileResponse("frontend/index.html")



@app.get("/")
async def root():

    #return FileResponse("frontend/index.html")

     return {
         "message": "System pomiarowy API",
         "version": "1.0",
         "status": "active"
     }

# Endpoint dla API info
@app.get("/api/info")
async def api_info():
    return {
        "message": "System pomiarowy API",
        "version": "1.0",
        "status": "active"
    }

logger.info("Lista wszystkich zarejestrowanych endpointów:")
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        logger.info(f"  {route.methods} {route.path}")










