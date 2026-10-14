# -*- coding: utf-8 -*-
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

class CryptoService:
    @staticmethod
    def decrypt(encrypted_data: str, password: str) -> str:
        """
        Descriptografa dados gerados pelo CryptoJS.AES.encrypt no Frontend.
        CryptoJS usa por padrao o formato 'Salted__' (formato OpenSSL).
        """
        try:
            data = base64.b64decode(encrypted_data)
            if data[:8] != b'Salted__':
                # Caso nao tenha salt, assume descriptografia simples
                return ""

            salt = data[8:16]
            ciphertext = data[16:]

            # Derivacao de Key e IV usando o metodo OpenSSL (EVP_BytesToKey)
            def derive_key_and_iv(pass_str, salt_bytes, key_len, iv_len):
                d = d_i = b''
                while len(d) < key_len + iv_len:
                    d_i = hashlib.md5(d_i + pass_str.encode('utf-8') + salt_bytes).digest()
                    d += d_i
                return d[:key_len], d[key_len:key_len + iv_len]

            key, iv = derive_key_and_iv(password, salt, 32, 16)
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            padded_plain = decryptor.update(ciphertext) + decryptor.finalize()
            unpadder = padding.PKCS7(128).unpadder()
            decrypted = unpadder.update(padded_plain) + unpadder.finalize()
            return decrypted.decode('utf-8')
        except Exception as e:
            print(f"Erro na descriptografia: {e}")
            return ""

crypto_service = CryptoService()

