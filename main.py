from fastapi import FastAPI
from database import init_db
from routers import todos, measure_data, aliases, static_params, integrator_prot, commands

# Inicjalizacja aplikacji FastAPI
app = FastAPI(title="System pomiarowy API")

# Inicjalizacja bazy danych
init_db()

# Dodanie routerów
app.include_router(todos.router)
app.include_router(measure_data.router)
app.include_router(aliases.router)
app.include_router(static_params.router)

app.include_router(commands.router)

@app.get("/")
async def root():
    return {
        "message": "System pomiarowy API",
        "version": "1.0",
        "status": "active"
    }

