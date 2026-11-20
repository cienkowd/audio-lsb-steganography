import config


class LSBSteganography:
    @staticmethod
    def text_to_bits(text):
        """Konwersja tekstu na listę bitów."""
        bits = []
        byte_data = text.encode(config.ENCODING)

        for byte in byte_data:
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)
        return bits

    @staticmethod
    def bits_to_text(bits):
        """Rekonstrukcja tekstu z bitów."""
        chars = []
        for i in range(0, len(bits), 8):
            byte_chunk = bits[i:i + 8]
            if len(byte_chunk) < 8:
                break

            byte_val = 0
            for bit_index, bit in enumerate(byte_chunk):
                byte_val |= (bit << (7 - bit_index))

            chars.append(byte_val)

        return bytes(chars).decode(config.ENCODING, errors='ignore')

    @staticmethod
    def embed_message(audio_data, message):
        """Ukrywa wiadomość w sygnale (LSB). Zwraca zmodyfikowaną kopię."""
        flat_audio = audio_data.flatten().copy()
        msg_bits = LSBSteganography.text_to_bits(message)

        # Nagłówek długości wiadomości
        msg_len = len(msg_bits)
        len_bits = [(msg_len >> i) & 1 for i in range(config.HEADER_SIZE - 1, -1, -1)]

        full_bits = len_bits + msg_bits
        total_bits_needed = len(full_bits)

        # Sprawdzenie pojemności
        capacity = len(flat_audio) * config.LSB_COUNT
        if total_bits_needed > capacity:
            raise ValueError(f"Wiadomość za długa: {total_bits_needed} > {capacity}")

        bit_idx = 0
        lsb_mask = (1 << config.LSB_COUNT) - 1

        for i in range(len(flat_audio)):
            if bit_idx >= total_bits_needed:
                break

            # Pobranie k bitów wiadomości
            chunk_val = 0
            for _ in range(config.LSB_COUNT):
                if bit_idx < total_bits_needed:
                    chunk_val = (chunk_val << 1) | full_bits[bit_idx]
                    bit_idx += 1
                else:
                    chunk_val = (chunk_val << 1)  # Padding zerami

            # Modyfikacja próbki: wyzerowanie końcówki -> wstawienie danych
            flat_audio[i] = (flat_audio[i] & ~lsb_mask) | chunk_val

        return flat_audio.reshape(audio_data.shape)

    @staticmethod
    def extract_message(audio_data):
        """Odczytuje ukrytą wiadomość (najpierw długość, potem treść)."""
        flat_audio = audio_data.flatten()
        lsb_mask = (1 << config.LSB_COUNT) - 1

        # 1. Odczyt nagłówka
        temp_bits = []
        msg_len = 0
        data_start = 0

        for i in range(len(flat_audio)):
            val = flat_audio[i] & lsb_mask

            for b in range(config.LSB_COUNT - 1, -1, -1):
                temp_bits.append((val >> b) & 1)

            if len(temp_bits) >= config.HEADER_SIZE:
                # Złożenie długości z bitów
                for bit in temp_bits[:config.HEADER_SIZE]:
                    msg_len = (msg_len << 1) | bit

                # Nadmiarowe bity idą do wiadomości
                extracted_bits = temp_bits[config.HEADER_SIZE:]
                data_start = i + 1
                break

        # 2. Odczyt treści
        current_count = len(extracted_bits)

        for i in range(data_start, len(flat_audio)):
            if current_count >= msg_len:
                break

            val = flat_audio[i] & lsb_mask
            for b in range(config.LSB_COUNT - 1, -1, -1):
                if current_count < msg_len:
                    extracted_bits.append((val >> b) & 1)
                    current_count += 1

        return LSBSteganography.bits_to_text(extracted_bits)