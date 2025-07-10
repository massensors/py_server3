import requests
from test import mojaFunkcjaTestowa


def test_analyze_endpoint():
    # Przygotuj dane testowe
    test_data = mojaFunkcjaTestowa("Massensors", "key2", 1000)

    # Wykonaj zapytanie POST
    response = requests.post(
        "http://localhost:8000/commands/analyze",
        data=test_data,
        headers={"Content-Type": "application/octet-stream"}
    )

    # Wyświetl wynik
    print("Status code:", response.status_code)
    print("Content-Type:", response.headers.get('content-type', ''))

    # Wyświetl zawartość odpowiedzi
    if response.headers.get('content-type') == 'application/octet-stream':
        # Dla odpowiedzi binarnej
        print("Response (hex):", response.content.hex(' '))
        print("Response length:", len(response.content), "bytes")

        # Wyświetl strukturę ramki
        print("\nFrame structure:")
        content = response.content
        print("HEADER:", content[:4].hex(' '))
        print("PLAIN:", content[4:21].hex(' '))
        print("ENCRYPTED:", content[21:-3].hex(' '))
        print("FOOTER:", content[-3:].hex(' '))
    else:
        # Dla odpowiedzi JSON
        try:
            print("Response (JSON):", response.json())
        except:
            print("Response (text):", response.text)


if __name__ == "__main__":
    test_analyze_endpoint()