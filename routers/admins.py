import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from starlette import status
from starlette.responses import HTMLResponse
from pydantic import BaseModel

from repositories.database import get_db
from models.models import Aliases,Users
from services.service_parameter_store import service_parameter_store

# Importuj funkcję weryfikacji tokenu osobno - bez USERS
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta

# Kopiuj dane użytkowników lokalnie (tymczasowe rozwiązanie)
# W przyszłości lepiej użyć bazy danych


# Dodaj modele Pydantic lokalnie
class UserCreateRequest(BaseModel):
    username: str
    role: str

class PasswordResetRequest(BaseModel):
    username: str

# Dodaj funkcję weryfikacji tokenu lokalnie
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
security = HTTPBearer()

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



# Konfiguracja loggera
logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={404: {"description": "Not found"}},
)


# NOWE ENDPOINTY ZARZĄDZANIA UŻYTKOWNIKAMI
@router.get("/users-management")
#async def users_management_page(current_user: str = Depends(verify_token)):
async def users_management_page():
    """Strona zarządzania użytkownikami - tylko dla adminów"""
    # Sprawdź czy użytkownik to admin
   # user = USERS.get(current_user)
   # if not user or user.get("role") != "admin":
   #     raise HTTPException(
   #         status_code=status.HTTP_403_FORBIDDEN,
   #         detail="Dostęp tylko dla administratorów"
   #     )

    html_content = """
    
            <!DOCTYPE html>
    <html lang="pl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Zarządzanie użytkownikami</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
            .users-container { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .user-form { background: white; padding: 20px; border-radius: 8px; border: 1px solid #ddd; }
            .form-group { margin-bottom: 15px; }
            .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
            .form-group input, .form-group select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
            .btn-primary { background: #007bff; color: white; }
            .btn-danger { background: #dc3545; color: white; }
            .btn-warning { background: #ffc107; color: black; }
            .btn-secondary { background: #6c757d; color: white; }
            .btn:hover { opacity: 0.9; }
            .user-item { display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid #ddd; }
            .user-info { flex-grow: 1; }
            .user-actions { display: flex; gap: 10px; }
            .role-badge { padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
            .role-admin { background: #dc3545; color: white; }
            .role-technik { background: #28a745; color: white; }
            .role-operator { background: #17a2b8; color: white; }
            .role-serwisant { background: #ffc107; color: black; }
            .message { padding: 10px; margin: 10px 0; border-radius: 4px; }
            .message.success { background: #d4edda; color: #155724; }
            .message.error { background: #f8d7da; color: #721c24; }
            .loading { text-align: center; padding: 50px; color: #6c757d; }
        </style>
    </head>
    <body>
        <div id="loading-screen" class="loading">
            <h2>Sprawdzanie uprawnień...</h2>
            <p>Proszę czekać...</p>
        </div>
        
        <div id="main-content" style="display: none;">
            <div class="header">
                <h1>Zarządzanie użytkownikami</h1>
                <button class="btn btn-secondary" onclick="window.location.href='/ui'">Powrót do aplikacji</button>
            </div>
            
            <div id="message-container"></div>
            
            <div class="users-container">
                <h2>Lista użytkowników</h2>
                <div id="users-list">
                    <div>Ładowanie...</div>
                </div>
            </div>
            
            <div class="user-form">
                <h2>Dodaj nowego użytkownika</h2>
                <form id="add-user-form">
                    <div class="form-group">
                        <label for="username">Nazwa użytkownika:</label>
                        <input type="text" id="username" required>
                    </div>
                    <div class="form-group">
                        <label for="role">Uprawnienia:</label>
                        <select id="role" required>
                            <option value="">Wybierz uprawnienia</option>
                            <option value="Operator">Operator</option>
                            <option value="Technik">Technik</option>
                            <option value="Serwisant">Serwisant</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary">Dodaj użytkownika</button>
                </form>
            </div>
        </div>
        
        <script>
            // DODAJ NA POCZĄTKU - Funkcja do wykonywania requestów z autoryzacją
            function fetchWithAuth(url, options = {}) {
                const token = localStorage.getItem('access_token');
                
                if (!token) {
                    window.location.href = '/login';
                    return Promise.reject('No token');
                }
                
                const authOptions = {
                    ...options,
                    headers: {
                        ...options.headers,
                        'Authorization': 'Bearer ' + token,
                        'Content-Type': 'application/json'
                    }
                };
                
                return fetch(url, authOptions).then(response => {
                    if (response.status === 401 || response.status === 403) {
                        localStorage.removeItem('access_token');
                        window.location.href = '/login';
                    }
                    return response;
                });
            }
            
            // Sprawdź autoryzację przy ładowaniu strony
            document.addEventListener('DOMContentLoaded', function() {
                const token = localStorage.getItem('access_token');
                
                if (!token) {
                    window.location.href = '/login';
                    return;
                }
                
                // Sprawdź czy token jest ważny
                fetchWithAuth('/api/user-info')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Token invalid');
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('User data:', data); // Debug
                    if (!data.is_admin) {
                        alert('Brak uprawnień administratora');
                        window.location.href = '/ui';
                        return;
                    }
                    
                    // Pokaż główną zawartość
                    document.getElementById('loading-screen').style.display = 'none';
                    document.getElementById('main-content').style.display = 'block';
                    
                    // Token ważny i użytkownik to admin - załaduj listę
                    loadUsers();
                })
                .catch(error => {
                    console.error('Błąd sprawdzania uprawnień:', error);
                    localStorage.removeItem('access_token');
                    window.location.href = '/login';
                });
            });
            // Funkcje pomocnicze
            function getAuthHeaders() {
                const token = localStorage.getItem('access_token');
                return {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                };
            }
            
            function showMessage(message, type = 'success') {
                const container = document.getElementById('message-container');
                container.innerHTML = `<div class="message ${type}">${message}</div>`;
                setTimeout(() => container.innerHTML = '', 5000);
            }
            
            // Załaduj listę użytkowników
            async function loadUsers() {
                try {
                    const response = await fetchWithAuth('/admin/users');
                    
                    if (!response.ok) throw new Error('Błąd ładowania użytkowników');
                    
                    const users = await response.json();
                    displayUsers(users);
                } catch (error) {
                    showMessage('Błąd ładowania użytkowników: ' + error.message, 'error');
                }
            }
            
            // Wyświetl użytkowników
            function displayUsers(users) {
                const container = document.getElementById('users-list');
                container.innerHTML = '';
                
                Object.entries(users).forEach(([username, user]) => {
                    const userDiv = document.createElement('div');
                    userDiv.className = 'user-item';
                    
                    const roleClass = `role-${user.role.toLowerCase()}`;
                    
                    userDiv.innerHTML = `
                        <div class="user-info">
                            <strong>${username}</strong>
                            <span class="role-badge ${roleClass}">${user.role}</span>
                        </div>
                        <div class="user-actions">
                            ${username !== 'admin' ? `
                                <button class="btn btn-warning" onclick="resetPassword('${username}')">Reset hasła</button>
                                <button class="btn btn-danger" onclick="deleteUser('${username}')">Usuń</button>
                            ` : '<span style="color: #6c757d;">Administrator główny</span>'}
                        </div>
                    `;
                    container.appendChild(userDiv);
                });
            }
            
            // Dodaj użytkownika
            document.getElementById('add-user-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const username = document.getElementById('username').value.trim();
                const role = document.getElementById('role').value;
                
                if (!username || !role) {
                    showMessage('Wypełnij wszystkie pola', 'error');
                    return;
                }
                
                try {
                    const response = await fetchWithAuth('/admin/users', {
                        method: 'POST',
                        body: JSON.stringify({ username, role })
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        showMessage(`Użytkownik ${username} został dodany. Hasło domyślne: 1234`);
                        document.getElementById('add-user-form').reset();
                        loadUsers();
                    } else {
                        showMessage(result.detail, 'error');
                    }
                } catch (error) {
                    showMessage('Błąd dodawania użytkownika: ' + error.message, 'error');
                }
            });
            
            // Reset hasła
            async function resetPassword(username) {
                if (!confirm(`Czy na pewno chcesz zresetować hasło użytkownika ${username}?`)) return;
                
                try {
                    const response = await fetchWithAuth('/admin/reset-password', {
                        method: 'POST',
                        body: JSON.stringify({ username })
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        showMessage(`Hasło użytkownika ${username} zostało zresetowane na: 1234`);
                    } else {
                        showMessage(result.detail, 'error');
                    }
                } catch (error) {
                    showMessage('Błąd resetowania hasła: ' + error.message, 'error');
                }
            }
            
            // Usuń użytkownika
            async function deleteUser(username) {
                if (!confirm(`Czy na pewno chcesz usunąć użytkownika ${username}?`)) return;
                
                try {
                    const response = await fetchWithAuth(`/admin/users/${username}`, {
                        method: 'DELETE'
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        showMessage(`Użytkownik ${username} został usunięty`);
                        loadUsers();
                    } else {
                        showMessage(result.detail, 'error');
                    }
                } catch (error) {
                    showMessage('Błąd usuwania użytkownika: ' + error.message, 'error');
                }
            }
        </script>
        
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/users")
async def get_users(current_user: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Pobierz listę użytkowników - tylko dla adminów"""
    user =  db.query(Users).filter(Users.username == current_user).first()
    if not user or user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dostęp tylko dla administratorów"
        )
    # Pobierz wszystkich użytkowników z bazy
    db_users = db.query(Users).all()

    # Usuń hasła z odpowiedzi i zachowaj strukturę słownika dla frontendu
    users_response = {}
    for u in db_users:
        users_response[u.username] = {
            "username": u.username,
            "role": u.role
        }

    return users_response

@router.post("/users")
async def create_user(request: UserCreateRequest, current_user: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Dodaj nowego użytkownika - tylko dla adminów"""
    user = db.query(Users).filter(Users.username == current_user).first()
    if not user or user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dostęp tylko dla administratorów"
        )

    # Sprawdź czy użytkownik już istnieje
    existing_user = db.query(Users).filter(Users.username == request.username).first()
    if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Użytkownik już istnieje"
            )

    # Sprawdź czy rola jest poprawna
    valid_roles = ["Operator", "Technik", "Serwisant"]
    if request.role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Niepoprawna rola. Dostępne: {', '.join(valid_roles)}"
            )

    # Dodaj użytkownika do bazy
    new_user = Users(
        username=request.username,
        password="User!BeltMate2025",  # Domyślne hasło
        role=request.role
    )
    db.add(new_user)
    db.commit()

    return {
            "status": "success",
            "message": f"Użytkownik {request.username} został dodany",
            "default_password": "User!BeltMate2025"
        }

@router.post("/reset-password")
async def reset_password(request: PasswordResetRequest, current_user: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Resetuj hasło użytkownika - tylko dla adminów"""
    user = db.query(Users).filter(Users.username == current_user).first()
    if not user or user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Dostęp tylko dla administratorów"
            )

    # Sprawdź czy użytkownik istnieje
    target_user = db.query(Users).filter(Users.username == request.username).first()
    if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Użytkownik nie istnieje"
            )

    # Nie pozwól na reset hasła admina
    if request.username == "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nie można zresetować hasła administratora głównego"
            )

    # Resetuj hasło
    target_user.password = "User!BeltMate2025"
    db.commit()

    return {
        "status": "success",
        "message": f"Hasło użytkownika {request.username} zostało zresetowane",
        "new_password": "User!BeltMate2025"
    }


@router.delete("/users/{username}")
async def delete_user(username: str, current_user: str = Depends(verify_token), db: Session = Depends(get_db)):
        """Usuń użytkownika - tylko dla adminów"""
        user = db.query(Users).filter(Users.username == current_user).first()
        if not user or user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Dostęp tylko dla administratorów"
            )

        # Nie pozwól na usunięcie admina
        if username == "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nie można usunąć administratora głównego"
            )

        # Sprawdź czy użytkownik istnieje
        target_user = db.query(Users).filter(Users.username == username).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Użytkownik nie istnieje"
            )

        # Usuń użytkownika
        db.delete(target_user)
        db.commit()

        return {
            "status": "success",
            "message": f"Użytkownik {username} został usunięty"
        }