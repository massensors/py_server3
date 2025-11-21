import logging
import  sys
from fastapi import FastAPI, Request, Depends, HTTPException, status, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta
from repositories.database import init_db




from repositories.database import init_db
from routers import measure_data, aliases, static_params, commands, app_interface, dynamic_readings, devices, \
    network_observer, admins
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

# Modele Pydantic dla requestów
class LoginRequest(BaseModel):
    username: str
    password: str

# Dane użytkownika (w produkcji używaj bazy danych)
USERS = {
    "admin": {
        "username": "admin",
        "password": "admin123",  # W produkcji używaj hashowanych haseł!
        "role": "admin"
    }
}


# Nowe modele Pydantic
#class UserCreateRequest(BaseModel):
#    username: str
#    role: str

#class UserUpdateRequest(BaseModel):
#    role: str

#class PasswordResetRequest(BaseModel):
#    username: str

security = HTTPBearer()
#templates = Jinja2Templates(directory="templates")


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
#-------------poczatek
# ... existing code ...
@app.get("/login")
async def login_page(request: Request):
    """Strona logowania"""
    html_content = """
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
            <div id="error-message" class="error" style="display: none;"></div>
            <form id="login-form">
                <input type="text" id="username" placeholder="Nazwa użytkownika" required>
                <input type="password" id="password" placeholder="Hasło" required>
                <button type="submit">Zaloguj się</button>
            </form>
            <p style="margin-top: 20px; font-size: 12px; color: #666;">
                Domyślne dane: admin / admin123
            </p>
        </div>
        
        <script>
            document.getElementById('login-form').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                const errorDiv = document.getElementById('error-message');
                
                try {
                    const response = await fetch('/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            username: username,
                            password: password
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (response.ok) {
                        localStorage.setItem('access_token', data.access_token);
                        window.location.href = '/ui';
                    } else {
                        errorDiv.textContent = data.detail || 'Błąd logowania';
                        errorDiv.style.display = 'block';
                    }
                } catch (error) {
                    errorDiv.textContent = 'Błąd połączenia';
                    errorDiv.style.display = 'block';
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/login")
async def login(login_data: LoginRequest):
    """Logowanie użytkownika"""
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowa nazwa użytkownika lub hasło"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

# ... existing code ...
#----------koniec

@app.get("/logout")
async def logout():
    """Wylogowanie użytkownika"""
    html_content = """
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
    return HTMLResponse(content=html_content)

# Dodanie routerów z wymaganiem uwierzytelniania

app.include_router(commands.router)

app.include_router(measure_data.router, dependencies=[Depends(verify_token)])
app.include_router(aliases.router, dependencies=[Depends(verify_token)])
app.include_router(static_params.router, dependencies=[Depends(verify_token)])
#app.include_router(commands.router, dependencies=[Depends(verify_token)])
app.include_router(app_interface.router, dependencies=[Depends(verify_token)])
app.include_router(service_mode_router, dependencies=[Depends(verify_token)])
app.include_router(dynamic_readings.router, dependencies=[Depends(verify_token)])
app.include_router(devices.router, dependencies=[Depends(verify_token)])
app.include_router(device_selection.router, dependencies=[Depends(verify_token)])
app.include_router(network_observer.router, dependencies=[Depends(verify_token)])
app.include_router(reports.router, prefix="/reports", tags=["reports"], dependencies=[Depends(verify_token)])
app.include_router(admins.router)
# ... existing code ...
# tu koniec nowego kodu








# Dodanie obsługi plików statycznych
#app.mount("/static", StaticFiles(directory="static"), name="static")
#app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")  # DODANE!

# Endpoint zwracający główny plik HTML interfejsu
# ------------poczatek
# ... existing code ...

# Endpoint zwracający główny plik HTML interfejsu
@app.get("/ui")
#async def get_ui(current_user: str = Depends(verify_token)):
async def get_ui():
    """Interfejs użytkownika - sprawdza token i zwraca frontend/index.html"""
    # Sprawdź czy plik frontend/index.html istnieje
    import os
    if not os.path.exists("frontend/index.html"):
        # Jeśli nie istnieje, zwróć prostą stronę błędu
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><title>Błąd</title></head>
        <body>
            <h1>Błąd</h1>
            <p>Nie znaleziono pliku frontend/index.html</p>
            <button onclick="window.location.href='/login'">Powrót do logowania</button>
        </body>
        </html>
        """)

    # Wczytaj oryginalny plik index.html
    with open("frontend/index.html", "r", encoding="utf-8") as file:
        original_content = file.read()

    # Dodaj skrypt autoryzacji i przycisk logout przed zamknięciem </body>
    auth_script = """
    <script>
        // Sprawdź autoryzację przy ładowaniu strony
        document.addEventListener('DOMContentLoaded', function() {
            const token = localStorage.getItem('access_token');
            
            if (!token) {
                // Brak tokena - przekieruj do logowania
                window.location.href = '/login';
                return;
            }
            
            // Sprawdź czy token jest ważny i pobierz dane użytkownika
            fetch('/api/user-info', {
                headers: {
                    'Authorization': 'Bearer ' + token
                }
            })
            .then(response => {
                if (!response.ok) {
                    // Token nieważny - wyczyść i przekieruj
                    localStorage.removeItem('access_token');
                    window.location.href = '/login';
                    return;
                }
                return response.json();
            })
            .then(data => {
                if (data && data.username) {
                    // Wyświetl informacje o użytkowniku
                    displayUserInfo(data.username, data.role);
                    
                    // Zapisz globalne informacje o użytkowniku
                    window.currentUser = data;
                    
                    // Dodaj przycisk zarządzania dla admina
                    if (data.is_admin) {
                        addAdminButton();
                    }    
                }
            })
            .catch(error => {
                console.error('Błąd sprawdzania tokena:', error);
                localStorage.removeItem('access_token');
                window.location.href = '/login';
            });
            
            // Dodaj przycisk logout jeśli jeszcze nie istnieje
            if (!document.getElementById('logout-btn')) {
                addLogoutButton();
            }
        });
        
        function displayUserInfo(username, role) {
            // Znajdź lub stwórz element dla informacji o użytkowniku
            let userInfo = document.getElementById('current-user-info');
            if (!userInfo) {
                // Stwórz element jeśli nie istnieje
                userInfo = document.createElement('div');
                userInfo.id = 'current-user-info';
                userInfo.style.cssText = `
                    position: absolute;
                    top: 20px;
                    left: 20px;
                    background: #f8f9fa;
                    padding: 8px 12px;
                    border-radius: 4px;
                    border: 1px solid #dee2e6;
                    font-size: 14px;
                    color: #495057;
                    z-index: 1000;
                `;
                
                // Dodaj do header
                const header = document.querySelector('header');
                if (header) {
                    header.appendChild(userInfo);
                } else {
                    document.body.appendChild(userInfo);
                }
            }
            
            const roleColor = role === 'admin' ? '#dc3545' : '#28a745';
            userInfo.innerHTML = `
                <span style="color: #28a745;">●</span> 
                Zalogowano jako: <strong>${username}</strong>  (${role})
            `;
        }
        function addAdminButton() {
            // Dodaj przycisk zarządzania użytkownikami dla admina
            const header = document.querySelector('header');
            if (!header || document.getElementById('admin-btn')) return;
            
            const adminBtn = document.createElement('button');
            adminBtn.id = 'admin-btn';
            adminBtn.textContent = ' Użytkownicy';
            adminBtn.style.cssText = `
                position: absolute;
                top: 60px;
                right: 20px;
                background: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                z-index: 1000;
            `;
            adminBtn.onmouseover = function() { this.style.background = '#218838'; };
            adminBtn.onmouseout = function() { this.style.background = '#28a745'; };
            adminBtn.onclick = function() {
                window.location.href = '/admin/users-management';
            };
            
            header.appendChild(adminBtn);
        }
        
        function addLogoutButton() {
            // Znajdź miejsce do wstawienia przycisku (np. w body lub konkretnym kontenerze)
            const body = document.body;
            
            // Stwórz kontener dla przycisku logout
            const logoutContainer = document.createElement('div');
            logoutContainer.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                z-index: 9999;
                background: white;
                padding: 10px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            `;
            
            // Stwórz przycisk logout
            const logoutBtn = document.createElement('button');
            logoutBtn.id = 'logout-btn';
            logoutBtn.textContent = 'Wyloguj';
            logoutBtn.style.cssText = `
                background: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            `;
            logoutBtn.onmouseover = function() { this.style.background = '#c82333'; };
            logoutBtn.onmouseout = function() { this.style.background = '#dc3545'; };
            logoutBtn.onclick = logout;
            
            logoutContainer.appendChild(logoutBtn);
            body.appendChild(logoutContainer);
        }
        
        function logout() {
            localStorage.removeItem('access_token');
            window.location.href = '/login';
        }
        
        // Funkcja pomocnicza do API calls z automatyczną autoryzacją
        window.authFetch = function(url, options = {}) {  // bylo window.authFetch =
            const token = localStorage.getItem('access_token');
            if (!token) {
                window.location.href = '/login';
                return Promise.reject('No token');
            }
            
            const authOptions = {
                ...options,
                headers: {
                    ...options.headers,
                    'Authorization': 'Bearer ' + token
                }
            };
            
            return fetch(url, authOptions).then(response => {
                if (response.status === 401 || response.status === 403) {
                    localStorage.removeItem('access_token');
                    window.location.href = '/login';
                }
                return response;
            });
        };
        
        window.fetchWithAuth = window.authFetch;
    </script>
    """

    # Wstaw skrypt przed zamknięciem </body>
    if "</body>" in original_content:
        modified_content = original_content.replace("</body>", auth_script)
    else:
        # Jeśli nie ma </body>, dodaj na koniec
        modified_content = original_content + auth_script + "</body>"

    return HTMLResponse(content=modified_content)

# ... existing code ...
#-------------koniec
@app.get("/ui-protected")
async def get_ui_protected(current_user: str = Depends(verify_token)):
    """Endpoint wymagający tokena w nagłówku (dla API calls)"""
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

# Endpoint do pobierania informacji o aktualnym użytkowniku (rozszerzony)
@app.get("/api/user-info")
async def get_user_info(current_user: str = Depends(verify_token)):
    """Pobierz szczegółowe informacje o aktualnym użytkowniku"""
    user_data = USERS.get(current_user)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Użytkownik nie istnieje"
        )

    return {
        "username": user_data["username"],
        "role": user_data["role"],
        "is_admin": user_data["role"] == "admin"
    }

logger.info("Lista wszystkich zarejestrowanych endpointów:")
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        logger.info(f"  {route.methods} {route.path}")










