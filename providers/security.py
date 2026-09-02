import base64
import hashlib
import logging
import os
import re
from google import genai
from cryptography.fernet import Fernet

logger = logging.getLogger("PIMSecurity")

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
    """Генерирует 32-байтный URL-safe Base64 ключ Fernet из секретной фразы."""
    hashed = hashlib.sha256(secret_passphrase.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(hashed)

def encrypt_secret(plain_text: str, secret_passphrase: str) -> str:
    """Зашифровывает данные с помощью AES-256 (Fernet) по секретному ключу."""
    if not plain_text or not secret_passphrase:
        return ""
    try:
        key = derive_fernet_key(secret_passphrase)
        cipher = Fernet(key)
        encrypted = cipher.encrypt(plain_text.encode('utf-8'))
        return encrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"🔴 Ошибка при шифровании: {e}")
        return ""

def decrypt_secret(encrypted_text: str, secret_passphrase: str) -> str:
    """Расшифровывает данные с помощью Fernet. Возвращает расшифрованную строку или сообщение об ошибке."""
    if not encrypted_text or not secret_passphrase:
        return ""
    try:
        key = derive_fernet_key(secret_passphrase)
        cipher = Fernet(key)
        decrypted = cipher.decrypt(encrypted_text.encode('utf-8'))
        return decrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"🔴 Ошибка при расшифровке (неверный ключ или поврежденные данные): {e}")
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
