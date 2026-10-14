import os
from anthropic import Anthropic
from dotenv import load_dotenv
from typing import Generator, List, Dict, Optional
from providers.security import sanitize_markdown

# Загружаем ключи из .env
load_dotenv()

def ask_anthropic(prompt: str, model_name: str = "claude-3-5-sonnet-20240620", system_prompt: Optional[str] = None) -> str:
    """
    Отправляет запрос к Anthropic Claude и возвращает ответ (синхронно).
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Не настроен ANTHROPIC_API_KEY.")

    try:
        client = Anthropic(api_key=api_key)
        kwargs = {
            "model": model_name,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = client.messages.create(**kwargs)
        return sanitize_markdown(response.content[0].text)
    except Exception as e:
        raise RuntimeError("Ошибка генерации Anthropic; проверьте настройки API и подключение.") from e


def stream_anthropic(messages: List[Dict[str, str]], model_name: str, temperature: float, max_tokens: int) -> Generator[str, None, None]:
    """
    Отправляет историю сообщений к Anthropic Claude и транслирует ответ в реальном времени.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Не настроен ANTHROPIC_API_KEY.")

    # Извлекаем системный промпт (Anthropic ожидает его отдельным аргументом)
    system_prompt = None
    api_messages = []
    for msg in messages:
        if msg["role"] == "system":
            system_prompt = msg["content"]
        else:
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

    kwargs = {
        "model": model_name,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": api_messages
    }
    if system_prompt:
        kwargs["system"] = system_prompt

    try:
        client = Anthropic(api_key=api_key)
        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as e:
        raise RuntimeError("Ошибка потоковой генерации Anthropic; проверьте настройки API и подключение.") from e


def list_available_anthropic_models() -> List[str]:
    """
    Получает список доступных моделей от Anthropic API.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return []
    try:
        client = Anthropic(api_key=api_key)
        # Проверяем наличие метода list
        if hasattr(client, 'models') and hasattr(client.models, 'list'):
            models_list = client.models.list()
            return [m.id for m in models_list.data]
        return []
    except Exception:
        return []
