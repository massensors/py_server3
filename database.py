from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from dotenv import load_dotenv


# Ładowanie zmiennych środowiskowych
load_dotenv()

# Konfiguracja bazy danych
DATABASE_NAME = 'measurement_system.db'
SQLALCHEMY_DATABASE_URL = f'sqlite:///./{DATABASE_NAME}'

# Utworzenie silnika bazy danych
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # Tylko dla SQLite
        "timeout": 30  # Timeout dla operacji bazodanowych
    }
)

# Konfiguracja sesji
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Klasa bazowa dla modeli
Base = declarative_base()

def init_db():
    """Inicjalizacja bazy danych i tworzenie wszystkich tabel"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """
    Generator do zarządzania sesją bazy danych.
    Zapewnia automatyczne zamykanie sesji po użyciu.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Inicjalizacja bazy przy imporcie modułu
init_db()