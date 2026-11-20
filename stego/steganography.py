from . import config


class LSBSteganography:
    @staticmethod
    def text_to_bits(text):
        """Convert text to a list of bits (MSB first)."""
        bits = []
        for byte in text.encode(config.ENCODING):
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)
        return bits

    @staticmethod
    def bits_to_text(bits):
        """Rebuild text from a list of bits."""
        chars = []
        for i in range(0, len(bits) - 7, 8):
            byte_val = 0
            for bit_index, bit in enumerate(bits[i:i + 8]):
                byte_val |= bit << (7 - bit_index)
            chars.append(byte_val)
        return bytes(chars).decode(config.ENCODING, errors="ignore")

    @staticmethod
    def capacity(audio_data):
        """Maximum message size in bits for this signal (excluding the header)."""
        return audio_data.size * config.LSB_COUNT - config.HEADER_SIZE

    @staticmethod
    def embed_message(audio_data, message):
        """Hide a message in the signal's least significant bits. Returns a modified copy."""
        flat_audio = audio_data.flatten().copy()
        msg_bits = LSBSteganography.text_to_bits(message)

        # Header: message length in bits
        msg_len = len(msg_bits)
        len_bits = [(msg_len >> i) & 1 for i in range(config.HEADER_SIZE - 1, -1, -1)]

        full_bits = len_bits + msg_bits
        total_bits_needed = len(full_bits)

        capacity = len(flat_audio) * config.LSB_COUNT
        if total_bits_needed > capacity:
            raise ValueError(f"Message too long: {total_bits_needed} bits > capacity {capacity} bits")

        bit_idx = 0
        lsb_mask = (1 << config.LSB_COUNT) - 1

        for i in range(len(flat_audio)):
            if bit_idx >= total_bits_needed:
                break

            # Take the next LSB_COUNT message bits
            chunk_val = 0
            for _ in range(config.LSB_COUNT):
                if bit_idx < total_bits_needed:
                    chunk_val = (chunk_val << 1) | full_bits[bit_idx]
                    bit_idx += 1
                else:
                    chunk_val <<= 1  # zero padding

            # Clear the low bits of the sample and write the message bits
            flat_audio[i] = (flat_audio[i] & ~lsb_mask) | chunk_val

        return flat_audio.reshape(audio_data.shape)

    @staticmethod
    def extract_message(audio_data):
        """Read a hidden message: first the length header, then the payload."""
        flat_audio = audio_data.flatten()
        lsb_mask = (1 << config.LSB_COUNT) - 1

        # 1. Header
        header_samples = -(-config.HEADER_SIZE // config.LSB_COUNT)  # ceil division
        if len(flat_audio) < header_samples:
            raise ValueError("Signal too short to contain a message header")

        bits = []
        for i in range(header_samples):
            val = int(flat_audio[i]) & lsb_mask
            for b in range(config.LSB_COUNT - 1, -1, -1):
                bits.append((val >> b) & 1)

        msg_len = 0
        for bit in bits[:config.HEADER_SIZE]:
            msg_len = (msg_len << 1) | bit
        if msg_len > LSBSteganography.capacity(audio_data):
            raise ValueError("No valid message found (length header out of range)")

        # Leftover header-sample bits already belong to the payload
        extracted_bits = bits[config.HEADER_SIZE:]

        # 2. Payload
        for i in range(header_samples, len(flat_audio)):
            if len(extracted_bits) >= msg_len:
                break
            val = int(flat_audio[i]) & lsb_mask
            for b in range(config.LSB_COUNT - 1, -1, -1):
                extracted_bits.append((val >> b) & 1)

        return LSBSteganography.bits_to_text(extracted_bits[:msg_len])
