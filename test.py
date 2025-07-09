import struct
from Crypto.Cipher import ARC4
from routers.commands import ProtocolAnalyzer


def mojaFunkcjaTestowa(key1: str, key2: str, iterations: int) -> bytes:
    # Przygotowanie danych
    header = bytes([0xAA, 0x55, 0x01, 0x01])  # START_MARKER1, START_MARKER2, VERSION=1, FLAGS=0 (nieszyfrowane)

    # Sekcja JAWNA (17 bajtów
    device_id = "2341".encode('ascii').ljust(10, b'\x00')  # 10 bajtów
    command_id = struct.pack('>H', 0x0003)  # 2 bajty, big-endian
    rc4_key_id = bytes([0x00])  # 1 bajt
    timestamp = bytes([0x00, 0x00, 0x00])  # 3 bajty
    seq_num = bytes([0x00])  # 1 bajt
    plain_section = device_id + command_id + rc4_key_id + timestamp + seq_num

    # Sekcja SZYFROWANA
    status = bytes([0x00])  # 1 bajt
    request = bytes([0x00])  # 1 bajt
    speed = "0.85".ljust(6).encode('ascii')  # 6 bajtów
    rate = "256.6".ljust(7).encode('ascii')  # 7 bajtów
    total = "12346".ljust(12).encode('ascii')  # 12 bajtów
    current_time = "2010-06-15 10:56:00".ljust(19).encode('ascii')  # 19 bajtów

    data = status + request + speed + rate + total + current_time
    data_len = bytes([len(data)])  # 1 bajt

    # Obliczanie CRC8 dla DATA_LEN + DATA
    data_to_crc8 = data_len + data
    crc8 = bytes([ProtocolAnalyzer.calculate_crc8(data_to_crc8)])  # 1 bajt

    encrypted_section = data_len + data + crc8

    if header[-1] == 1:

        data = encrypted_section
        # Obliczamy klucz na podstawie key1 i key2
        key = ProtocolAnalyzer._calculate_key(key1, key2, iterations)
        # Inicjalizacja szyfru ARC4
        cipher = ARC4.new(key)
        # Szyfrowanie danych
        encrypted_section = cipher.encrypt(data)
        frame_without_footer = header + plain_section + encrypted_section
        crc16 = struct.pack('>H', ProtocolAnalyzer.calculate_crc16(frame_without_footer))  # 2 bajty
    else:
        # Składanie całej ramki
        frame_without_footer = header + plain_section + encrypted_section

        # Obliczanie CRC16 dla całości bez FOOTER
        crc16 = struct.pack('>H', ProtocolAnalyzer.calculate_crc16(frame_without_footer))  # 2 bajty

        # Dodanie FOOTER
    footer = crc16 + bytes([0x55])  # END_MARKER
    # Kompletna ramka
    complete_frame = frame_without_footer + footer

    return complete_frame