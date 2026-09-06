"""
🏛️ Citadel Oracle PIM — Тесты Безопасности и Криптографии
Проверка функций шифрования AES-256 Fernet, санитизации Markdown и валидации API-ключа Gemini.
"""

import unittest
from unittest.mock import patch, MagicMock
from providers.security import (
    derive_fernet_key,
    encrypt_secret,
    decrypt_secret,
    sanitize_markdown,
    verify_gemini_api_key,
)


class TestSecurityCryptography(unittest.TestCase):
    """Набор тестов для криптографического модуля Сейфа Цитадели."""

    def setUp(self):
        self.passphrase = "shekinah_citadel_master_passphrase_2026"
        self.secret_data = "AIzaSyTestSecretTokenCitadel_123456789!@#$%^&*()"

    def test_derive_fernet_key_deterministic(self):
        """Проверка детерминированности деривации ключа Fernet."""
        key1 = derive_fernet_key(self.passphrase)
        key2 = derive_fernet_key(self.passphrase)
        self.assertEqual(key1, key2, "Ключ из одинаковой фразы должен быть абсолютно идентичным")
        self.assertIsInstance(key1, bytes)
        # Длина Fernet Base64 ключа всегда составляет 44 символа (32 байта в base64)
        self.assertEqual(len(key1), 44)

    def test_derive_fernet_key_avalanche_effect(self):
        """Проверка лавинного эффекта при изменении хотя бы одного символа в ключе."""
        key1 = derive_fernet_key(self.passphrase)
        key2 = derive_fernet_key(self.passphrase + "!")
        self.assertNotEqual(key1, key2, "Изменение пароля должно приводить к совершенно иному ключу")

    def test_encrypt_decrypt_roundtrip(self):
        """Проверка полного цикла шифрования и расшифровки данных."""
        encrypted = encrypt_secret(self.secret_data, self.passphrase)
        self.assertTrue(bool(encrypted), "Зашифрованная строка не должна быть пустой")
        self.assertNotEqual(encrypted, self.secret_data, "Шифротекст должен отличаться от исходного текста")

        decrypted = decrypt_secret(encrypted, self.passphrase)
        self.assertEqual(decrypted, self.secret_data, "Расшифрованный текст должен строго совпадать с исходным")

    def test_encrypt_decrypt_unicode_multiline(self):
        """Проверка шифрования многострочного текста с кириллицей и эмодзи."""
        unicode_payload = "🏛️ Священный Свиток Цитадели\nПароль: 12345\nЗаметка: Миссия Шехина Казахстан 🇰🇿"
        encrypted = encrypt_secret(unicode_payload, self.passphrase)
        decrypted = decrypt_secret(encrypted, self.passphrase)
        self.assertEqual(decrypted, unicode_payload)

    def test_decrypt_with_wrong_passphrase(self):
        """Проверка безопасной обработки попытки расшифровки с неверным паролем."""
        encrypted = encrypt_secret(self.secret_data, self.passphrase)
        decrypted_fail = decrypt_secret(encrypted, "wrong_sacred_passphrase")
        self.assertEqual(decrypted_fail, "[Ошибка: Неверный ключ расшифровки]")

    def test_decrypt_with_corrupted_ciphertext(self):
        """Проверка обработки поврежденного шифротекста."""
        decrypted = decrypt_secret("not_a_valid_fernet_token_corrupted", self.passphrase)
        self.assertEqual(decrypted, "[Ошибка: Неверный ключ расшифровки]")

    def test_empty_inputs_graceful(self):
        """Проверка передачи пустых строк и None."""
        self.assertEqual(encrypt_secret("", self.passphrase), "")
        self.assertEqual(encrypt_secret(self.secret_data, ""), "")
        self.assertEqual(decrypt_secret("", self.passphrase), "")
        self.assertEqual(decrypt_secret(self.secret_data, ""), "")


class TestMarkdownSanitization(unittest.TestCase):
    """Набор тестов для функции sanitize_markdown."""

    def test_empty_and_none(self):
        """Проверка обработки пустых строк."""
        self.assertEqual(sanitize_markdown(""), "")
        self.assertEqual(sanitize_markdown(None), "")

    def test_table_separator_compression(self):
        """Проверка сжатия избыточных цепочек дефисов в разделителях таблиц."""
        # Разделители вида :------:
        input_text = "| Колонка 1 | Колонка 2 |\n|:----------:|:---------|\n| Данные 1 | Данные 2 |"
        sanitized = sanitize_markdown(input_text)
        self.assertIn(":---:", sanitized)
        self.assertNotIn(":----------:", sanitized)

    def test_multiple_hyphens_compression(self):
        """Проверка сжатия длинных цепочек дефисов и тире."""
        input_text = "Разделитель: " + "-" * 50 + " Конец"
        sanitized = sanitize_markdown(input_text)
        self.assertIn("---", sanitized)
        self.assertNotIn("-" * 10, sanitized)

    def test_multiple_underscores_and_equals(self):
        """Проверка сжатия подчеркиваний и знаков равенства."""
        text_with_underscores = "Линия: " + "_" * 20
        text_with_equals = "Заголовок: " + "=" * 20
        self.assertEqual(sanitize_markdown(text_with_underscores), "Линия: ___")
        self.assertEqual(sanitize_markdown(text_with_equals), "Заголовок: ===")

    def test_multiple_dots_and_spaces(self):
        """Проверка сжатия избыточных многоточий и длинных цепочек пробелов."""
        text_dots = "Размышления" + "." * 15
        text_spaces = "Слово1" + " " * 20 + "Слово2"
        self.assertEqual(sanitize_markdown(text_dots), "Размышления...")
        self.assertEqual(sanitize_markdown(text_spaces), "Слово1    Слово2")


class TestGeminiApiKeyValidation(unittest.TestCase):
    """Набор тестов для валидатора ключа Google Gemini."""

    def test_short_or_empty_key(self):
        """Проверка отклонения слишком коротких ключей."""
        valid, msg = verify_gemini_api_key("")
        self.assertFalse(valid)
        self.assertIn("слишком короткий", msg)

        valid, msg = verify_gemini_api_key("1234567")
        self.assertFalse(valid)

    @patch("providers.security.genai.Client")
    def test_valid_key_success(self, mock_client_cls):
        """Проверка успешной валидации ключа при наличии моделей."""
        mock_instance = MagicMock()
        mock_instance.models.list.return_value = ["gemini-2.5-flash", "gemini-2.5-pro"]
        mock_client_cls.return_value = mock_instance

        valid, msg = verify_gemini_api_key("AIzaSyValidGeminiKeyFormat123456789")
        self.assertTrue(valid)
        self.assertIn("Ключ подлинный", msg)
        self.assertIn("2", msg)

    @patch("providers.security.genai.Client")
    def test_valid_key_empty_models(self, mock_client_cls):
        """Проверка ответа при пустом списке моделей."""
        mock_instance = MagicMock()
        mock_instance.models.list.return_value = []
        mock_client_cls.return_value = mock_instance

        valid, msg = verify_gemini_api_key("AIzaSyValidGeminiKeyFormat123456789")
        self.assertFalse(valid)
        self.assertIn("Не удалось получить список моделей", msg)

    @patch("providers.security.genai.Client")
    def test_invalid_key_api_error(self, mock_client_cls):
        """Проверка обработки исключения API_KEY_INVALID."""
        mock_instance = MagicMock()
        mock_instance.models.list.side_effect = Exception("API_KEY_INVALID: The provided API key is expired or invalid.")
        mock_client_cls.return_value = mock_instance

        valid, msg = verify_gemini_api_key("AIzaSyInvalidKey12345678900000")
        self.assertFalse(valid)
        self.assertIn("недействителен или заблокирован", msg)


if __name__ == "__main__":
    unittest.main()
