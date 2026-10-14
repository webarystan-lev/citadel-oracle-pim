import base64
import hashlib
import logging
import os
import re
import secrets
from google import genai
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

logger = logging.getLogger("PIMSecurity")
_KDF_PREFIX = "pim2"
_KDF_ITERATIONS = 600_000
_KDF_SALT_BYTES = 16

def sanitize_markdown(text: str) -> str:
    """
    Очищает и форматирует Markdown-текст, сжимая аномальные повторы символов
    (дефисы, тире, подчеркивания, знаки равенства, пробелы), которые могут
    вызывать зависание браузера или ломать верстку таблиц.
    """
    if not text:
        return ""
    
    # 1. Сжатие длинных разделителей в таблицах :----: или :--- или ---:
    text = re.sub(r':-{3,}:', ':---:', text)
    text = re.sub(r':-{3,}', ':---', text)
    text = re.sub(r'-{3,}:', '---:', text)
    
    # 2. Сжатие любых длинных последовательностей дефисов/тире (4 и более подряд)
    text = re.sub(r'[-—–]{4,}', '---', text)
    
    # 3. Сжатие длинных цепочек подчеркиваний и знаков равенства
    text = re.sub(r'_{4,}', '___', text)
    text = re.sub(r'={4,}', '===', text)
    
    # 4. Сжатие многоточий (более 3 точек подряд)
    text = re.sub(r'\.{4,}', '...', text)
    
    # 5. Сжатие аномально длинных цепочек пробелов (более 8 подряд)
    text = re.sub(r'[ ]{8,}', '    ', text)
    
    return text


def derive_fernet_key(secret_passphrase: str) -> bytes:
    """Derive a Fernet key from a passphrase using a randomly salted PBKDF2 key."""
    salt = secrets.token_bytes(_KDF_SALT_BYTES)
    return _derive_salted_fernet_key(secret_passphrase, salt)


def _derive_salted_fernet_key(secret_passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_KDF_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(secret_passphrase.encode("utf-8")))


def _derive_legacy_fernet_key(secret_passphrase: str) -> bytes:
    return base64.urlsafe_b64encode(hashlib.sha256(secret_passphrase.encode("utf-8")).digest())

def encrypt_secret(plain_text: str, secret_passphrase: str) -> str:
    """Encrypt with Fernet using a fresh, salted PBKDF2-derived key."""
    if not plain_text or not secret_passphrase:
        return ""
    try:
        salt = secrets.token_bytes(_KDF_SALT_BYTES)
        key = _derive_salted_fernet_key(secret_passphrase, salt)
        cipher = Fernet(key)
        encrypted = cipher.encrypt(plain_text.encode('utf-8'))
        return "$".join((_KDF_PREFIX, base64.urlsafe_b64encode(salt).decode("ascii"), encrypted.decode("ascii")))
    except Exception as e:
        logger.error("🔴 Ошибка при шифровании: %s", type(e).__name__)
        raise RuntimeError("Не удалось зашифровать секрет.") from e

def decrypt_secret(encrypted_text: str, secret_passphrase: str) -> str:
    """Decrypt current salted records and legacy SHA-256 records."""
    if not encrypted_text or not secret_passphrase:
        return ""
    try:
        if encrypted_text.startswith(f"{_KDF_PREFIX}$"):
            _, encoded_salt, token = encrypted_text.split("$", 2)
            salt = base64.urlsafe_b64decode(encoded_salt.encode("ascii"))
            if len(salt) != _KDF_SALT_BYTES:
                raise ValueError("Invalid KDF salt")
            key = _derive_salted_fernet_key(secret_passphrase, salt)
        else:
            token = encrypted_text
            key = _derive_legacy_fernet_key(secret_passphrase)
        cipher = Fernet(key)
        decrypted = cipher.decrypt(token.encode('ascii'))
        return decrypted.decode('utf-8')
    except (InvalidToken, ValueError, UnicodeDecodeError, UnicodeEncodeError) as e:
        logger.warning("🔴 Ошибка при расшифровке (неверный ключ или поврежденные данные): %s", type(e).__name__)
        return "[Ошибка: Неверный ключ расшифровки]"

def verify_gemini_api_key(api_key: str) -> tuple[bool, str]:
    """
    Проверяет валидность GEMINI_API_KEY путём официального вызова client.models.list() (новый SDK google-genai).
    Возвращает (True, "Успешно") или (False, "Сообщение об ошибке").
    """
    if not api_key or len(api_key.strip()) < 10:
        return False, "Ключ GEMINI_API_KEY слишком короткий или отсутствует."
    
    try:
        client = genai.Client(api_key=api_key.strip())
        # Делаем минимальный вызов списка моделей через современный клиент
        models = list(client.models.list())
        if models and len(models) > 0:
            return True, f"Ключ подлинный. Доступно моделей Google Gemini: {len(models)}"
        return False, "Не удалось получить список моделей Google."
    except Exception as e:
        err_msg = str(e)
        if "API_KEY_INVALID" in err_msg or "400" in err_msg or "403" in err_msg:
            return False, "API-ключ Google Gemini недействителен или заблокирован."
        return False, f"Ошибка проверки API-ключа Google: {err_msg[:120]}"
