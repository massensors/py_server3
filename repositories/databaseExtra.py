from typing import Dict, Any
import json
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, inspect

from database import engine, DATABASE_NAME, SQLALCHEMY_DATABASE_URL


def inspect_database() -> Dict[str, Any]:
    """
    Kompleksowa inspekcja bazy danych.
    Zwraca szczegółowe informacje o strukturze bazy danych.
    """
    inspector = inspect(engine)

    database_info = {
        "database_name": DATABASE_NAME,
        "database_url": SQLALCHEMY_DATABASE_URL,
        "tables": {},
        "summary": {}
    }

    # Pobierz wszystkie tabele
    table_names = inspector.get_table_names()
    database_info["summary"]["total_tables"] = len(table_names)
    database_info["summary"]["table_list"] = table_names

    # Szczegółowe informacje o każdej tabeli
    for table_name in table_names:
        table_info = {
            "columns": [],
            "primary_keys": [],
            "foreign_keys": [],
            "indexes": [],
            "column_count": 0
        }

        # Informacje o kolumnach
        columns = inspector.get_columns(table_name)
        table_info["column_count"] = len(columns)

        for column in columns:
            column_info = {
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": column["nullable"],
                "default": str(column["default"]) if column["default"] else None,
                "autoincrement": column.get("autoincrement", False)
            }
            table_info["columns"].append(column_info)

        # Klucze główne
        primary_keys = inspector.get_primary_keys(table_name)
        table_info["primary_keys"] = primary_keys

        # Klucze obce
        foreign_keys = inspector.get_foreign_keys(table_name)
        for fk in foreign_keys:
            fk_info = {
                "name": fk["name"],
                "constrained_columns": fk["constrained_columns"],
                "referred_table": fk["referred_table"],
                "referred_columns": fk["referred_columns"]
            }
            table_info["foreign_keys"].append(fk_info)

        # Indeksy
        indexes = inspector.get_indexes(table_name)
        for index in indexes:
            index_info = {
                "name": index["name"],
                "column_names": index["column_names"],
                "unique": index["unique"]
            }
            table_info["indexes"].append(index_info)

        database_info["tables"][table_name] = table_info

    return database_info


def verify_tables() -> Dict[str, Any]:
    """
    Sprawdza czy wszystkie wymagane tabele istnieją w bazie danych.
    Zwraca szczegółowy raport o statusie tabel.
    """
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    required_tables = ['todos', 'MeasureData', 'Aliases', 'StaticParams']

    missing_tables = [table for table in required_tables if table not in existing_tables]
    extra_tables = [table for table in existing_tables if table not in required_tables]

    verification_report = {
        "status": "OK" if not missing_tables else "MISSING_TABLES",
        "existing_tables": existing_tables,
        "required_tables": required_tables,
        "missing_tables": missing_tables,
        "extra_tables": extra_tables,
        "total_existing": len(existing_tables),
        "total_required": len(required_tables)
    }

    if missing_tables:
        print(f"⚠️  Ostrzeżenie: Brakujące tabele: {missing_tables}")

    if extra_tables:
        print(f"ℹ️  Informacja: Dodatkowe tabele: {extra_tables}")

    return verification_report


def get_table_info(table_name: str) -> Dict[str, Any]:
    """
    Pobiera szczegółowe informacje o konkretnej tabeli.

    Args:
        table_name: Nazwa tabeli do sprawdzenia

    Returns:
        Słownik z informacjami o tabeli
    """
    inspector = inspect(engine)

    if table_name not in inspector.get_table_names():
        return {"error": f"Tabela '{table_name}' nie istnieje"}

    table_info = {
        "table_name": table_name,
        "columns": inspector.get_columns(table_name),
        "primary_keys": inspector.get_primary_keys(table_name),
        "foreign_keys": inspector.get_foreign_keys(table_name),
        "indexes": inspector.get_indexes(table_name),
        "column_count": len(inspector.get_columns(table_name))
    }

    return table_info


def export_schema_to_json(filepath: str = "database_schema.json") -> bool:
    """
    Eksportuje schemat bazy danych do pliku JSON.

    Args:
        filepath: Ścieżka do pliku JSON

    Returns:
        True jeśli eksport się powiódł, False w przeciwnym razie
    """
    try:
        schema_info = inspect_database()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(schema_info, f, indent=2, ensure_ascii=False)
        print(f"✅ Schemat bazy danych wyeksportowany do: {filepath}")
        return True
    except Exception as e:
        print(f"❌ Błąd eksportu schematu: {str(e)}")
        return False


def print_database_summary():
    """
    Wyświetla podsumowanie bazy danych w konsoli.
    """
    info = inspect_database()
    print("\n" + "=" * 50)
    print("PODSUMOWANIE BAZY DANYCH")
    print("=" * 50)
    print(f"Nazwa bazy: {info['database_name']}")
    print(f"Liczba tabel: {info['summary']['total_tables']}")
    print(f"Tabele: {', '.join(info['summary']['table_list'])}")

    print("\nSzczegóły tabel:")
    for table_name, table_info in info['tables'].items():
        print(f"\n📋 {table_name}:")
        print(f"   - Kolumny: {table_info['column_count']}")
        print(f"   - Klucze główne: {', '.join(table_info['primary_keys'])}")
        print(f"   - Klucze obce: {len(table_info['foreign_keys'])}")
        print(f"   - Indeksy: {len(table_info['indexes'])}")

    print("\n" + "=" * 50)
