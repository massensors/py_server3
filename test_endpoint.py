import requests
from test import mojaFunkcjaTestowa


def test_analyze_endpoint():
    # Przygotuj dane testowe
    test_data = mojaFunkcjaTestowa("Massensors","key2",1000)

    # Wykonaj zapytanie POST
    response = requests.post(
        "http://localhost:8000/commands/analyze",
        data=test_data,
        headers={"Content-Type": "application/octet-stream"}
    )

    # Wyświetl wynik
    print("Status code:", response.status_code)
    print("Response:", response.json())


if __name__ == "__main__":
    test_analyze_endpoint()