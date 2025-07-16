import hashlib
from Crypto.Cipher import ARC4
from typing import Union, Optional


class RC4KeyGenerator:
    DEFAULT_ITERATIONS = 1000

    @staticmethod
    def generate_key(key1: Union[str, bytes, list],
                     key2: Optional[Union[str, bytes, list]] = None,
                     iterations: int = DEFAULT_ITERATIONS) -> bytes:
        """
        Generuje klucz RC4 na podstawie podanych parametrów.

        Args:
            key1: Pierwszy klucz (string, bytes lub lista intów)
            key2: Opcjonalny drugi klucz (string, bytes lub lista intów)
            iterations: Liczba iteracji dla SHA256 (domyślnie 1000)

        Returns:
            bytes: Wygenerowany klucz RC4
        """
        # Konwersja kluczy na bytes
        key1_bytes = RC4KeyGenerator._convert_to_bytes(key1)

        if key2 is None:
            # Jeśli podano tylko jeden klucz, użyj go bezpośrednio
            return key1_bytes

        # Konwersja drugiego klucza na bytes
        key2_bytes = RC4KeyGenerator._convert_to_bytes(key2)

        # Początkowy hash: key = SHA256(key1 . key2)
        key = hashlib.sha256(key1_bytes + key2_bytes).digest()

        # Iteracyjne wzmacnianie klucza
        for _ in range(iterations):
            # key = SHA256(key . key1 . key2)
            combined = key + key1_bytes + key2_bytes
            key = hashlib.sha256(combined).digest()

        return key

    @staticmethod
    def _convert_to_bytes(key: Union[str, bytes, list]) -> bytes:
        """
        Konwertuje różne formaty klucza na bytes.

        Args:
            key: Klucz w formie string, bytes lub listy intów

        Returns:
            bytes: Skonwertowany klucz
        """
        if isinstance(key, str):
            return key.encode('utf-8')
        elif isinstance(key, bytes):
            return key
        elif isinstance(key, list):
            return bytes(key)
        else:
            raise ValueError("Nieobsługiwany format klucza")

    @staticmethod
    def create_cipher(key1: Union[str, bytes, list],
                      key2: Optional[Union[str, bytes, list]] = None,
                      iterations: int = DEFAULT_ITERATIONS) -> ARC4:
        """
        Tworzy obiekt szyfru RC4 z wygenerowanym kluczem.

        Args:
            key1: Pierwszy klucz
            key2: Opcjonalny drugi klucz
            iterations: Liczba iteracji dla SHA256

        Returns:
            ARC4: Skonfigurowany obiekt szyfru RC4
        """
        key = RC4KeyGenerator.generate_key(key1, key2, iterations)
        return ARC4.new(key)