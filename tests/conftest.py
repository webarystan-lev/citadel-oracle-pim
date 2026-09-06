"""
🏛️ Citadel Oracle PIM — Fixtures & Test Setup
Общие фикстуры для тестирования компонентов Цитадели через pytest и unittest.
"""

import os
import pytest

@pytest.fixture
def test_passphrase() -> str:
    """Фикстура тестовой парольной фразы Цитадели."""
    return "shekinah_citadel_sacred_passphrase_2026"

@pytest.fixture
def test_secret_data() -> str:
    """Фикстура секретных данных для тестирования Сейфа."""
    return "AIzaSyCitadelOracleTestSecretPayload123456789"

@pytest.fixture
def isolated_env(monkeypatch):
    """Изолированное окружение для предотвращения обращения к боевым сервисам."""
    monkeypatch.setenv("CONVEX_URL", "https://test-citadel.convex.cloud")
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_api_key_valid_12345")
    monkeypatch.setenv("PIM_SECRET_KEY", "citadel_test_master_key_2026")
    yield monkeypatch
