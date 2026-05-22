# -*- coding: utf-8 -*-
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from Crypto.Protocol.KDF import PBKDF2
import hashlib

class CryptoService:
    @staticmethod
    def decrypt(encrypted_data: str, password: str) -> str:
        """
        Descriptografa dados gerados pelo CryptoJS.AES.encrypt no Frontend.
        CryptoJS usa por padrão o formato 'Salted__' (formato OpenSSL).
        """
        try:
            data = base64.b64decode(encrypted_data)
            if data[:8] != b'Salted__':
                # Caso não tenha salt, assume descriptografia simples (raro no CryptoJS padrão)
                return ""

            salt = data[8:16]
            ciphertext = data[16:]

            # Derivação de Key e IV usando o método OpenSSL (EVP_BytesToKey)
            # CryptoJS usa MD5 por padrão na derivação legada ou PBKDF2.
            # Para manter simples e robusto, o CryptoJS moderno permite especificar KDF.
            # Se usarmos o padrão do CryptoJS sem params extras, ele faz o seguinte:
            
            def derive_key_and_iv(password, salt, key_len, iv_len):
                d = d_i = b''
                while len(d) < key_len + iv_len:
                    d_i = hashlib.md5(d_i + password.encode('utf-8') + salt).digest()
                    d += d_i
                return d[:key_len], d[key_len:key_len + iv_len]

            key, iv = derive_key_and_iv(password, salt, 32, 16)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
            return decrypted.decode('utf-8')
        except Exception as e:
            print(f"Erro na descriptografia: {e}")
            return ""

crypto_service = CryptoService()
