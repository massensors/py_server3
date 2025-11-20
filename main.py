import logging
import  sys
from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.templating import Jinja2Templates
import jwt
from datetime import datetime, timedelta
from repositories.database import init_db




from repositories.database import init_db
from routers import measure_data, aliases, static_params, commands, app_interface, dynamic_readings, devices, \
    network_observer
from routers.service_mode import router as service_mode_router
from routers import device_selection
from routers import measure_data
from routers import reports


import uvicorn
# przed dodaniem uwierzytelnienia
# pierwsze kroki uwierzytelnienia
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

# Konfiguracja uwierzytelniania
SECRET_KEY = "your-secret-key-change-in-production"  # ZMIEŃ TO W PRODUKCJI!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Dane użytkownika (w produkcji używaj bazy danych)
USERS = {
    "admin": {
        "username": "admin",
        "password": "admin123",  # W produkcji używaj hashowanych haseł!
        "role": "admin"
    }
}

security = HTTPBearer()
templates = Jinja2Templates(directory="templates")


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def authenticate_user(username: str, password: str):
    user = USERS.get(username)
    if not user or user["password"] != password:
        return False
    return user

# Usuń wszystkie handlery

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
# tu nowy kod


# Endpointy logowania
@app.get("/login")
async def login_page(request: Request):
    """Strona logowania"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Logowanie - System pomiarowy</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 400px; margin: 100px auto; padding: 20px; }
            .login-form { border: 1px solid #ddd; padding: 30px; border-radius: 8px; }
            input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; }
            button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .error { color: red; margin: 10px 0; }
            h2 { text-align: center; color: #333; }
        </style>
    </head>
    <body>
        <div class="login-form">
            <h2>Logowanie do systemu</h2>
            <form method="post" action="/login">
                <input type="text" name="username" placeholder="Nazwa użytkownika" required>
                <input type="password" name="password" placeholder="Hasło" required>
                <button type="submit">Zaloguj się</button>
            </form>
            <p style="margin-top: 20px; font-size: 12px; color: #666;">
                Domyślne dane: admin / admin123
            </p>
        </div>
    </body>
    </html>
    """


@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    """Logowanie użytkownika"""
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowa nazwa użytkownika lub hasło"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )

    # Przekierowanie do interfejsu z tokenem w localStorage
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Logowanie...</title>
    </head>
    <body>
        <script>
            localStorage.setItem('access_token', '{access_token}');
            window.location.href = '/ui';
        </script>
        <p>Logowanie zakończone sukcesem. Przekierowywanie...</p>
    </body>
    </html>
    """


@app.get("/logout")
async def logout():
    """Wylogowanie użytkownika"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Wylogowanie</title>
    </head>
    <body>
        <script>
            localStorage.removeItem('access_token');
            window.location.href = '/login';
        </script>
        <p>Wylogowywanie...</p>
    </body>
    </html>
    """


# Dodanie routerów z wymaganiem uwierzytelniania
app.include_router(measure_data.router, dependencies=[Depends(verify_token)])
app.include_router(aliases.router, dependencies=[Depends(verify_token)])
app.include_router(static_params.router, dependencies=[Depends(verify_token)])
app.include_router(commands.router, dependencies=[Depends(verify_token)])
app.include_router(app_interface.router, dependencies=[Depends(verify_token)])
app.include_router(service_mode_router, dependencies=[Depends(verify_token)])
app.include_router(dynamic_readings.router, dependencies=[Depends(verify_token)])
app.include_router(devices.router, dependencies=[Depends(verify_token)])
app.include_router(device_selection.router, dependencies=[Depends(verify_token)])
app.include_router(network_observer.router, dependencies=[Depends(verify_token)])
app.include_router(reports.router, prefix="/reports", tags=["reports"], dependencies=[Depends(verify_token)])

# ... existing code ...
# tu koniec nowego kodu








# Dodanie obsługi plików statycznych
#app.mount("/static", StaticFiles(directory="static"), name="static")
#app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")  # DODANE!

# Endpoint zwracający główny plik HTML interfejsu
@app.get("/ui")
#async def get_ui():
async def get_ui(current_user: str = Depends(verify_token)):
    #return FileResponse("static/index.html")
    return FileResponse("frontend/index.html")



@app.get("/")
async def root():
    # Przekierowanie do strony logowania
    return RedirectResponse(url="/login")

# Endpoint dla API info
@app.get("/api/info")
async def api_info(current_user: str = Depends(verify_token)):
    return {
        "message": "System pomiarowy API",
        "version": "1.0",
        "status": "active",
        "user": current_user
    }

logger.info("Lista wszystkich zarejestrowanych endpointów:")
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        logger.info(f"  {route.methods} {route.path}")










