import os
from anthropic import Anthropic
from dotenv import load_dotenv
from typing import Generator, List, Dict

# Загружаем ключи из .env
load_dotenv()

def ask_anthropic(prompt: str, model_name: str = "claude-3-5-sonnet-20240620") -> str:
    """
    Отправляет запрос к Anthropic Claude и возвращает ответ (синхронно).
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "Ошибка: не найден ANTHROPIC_API_KEY в .env"

    client = Anthropic(api_key=api_key)

    response = client.messages.create(
        model=model_name,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    # Ответ приходит в виде списка блоков
    return response.content[0].text


def stream_anthropic(messages: List[Dict[str, str]], model_name: str, temperature: float, max_tokens: int) -> Generator[str, None, None]:
    """
    Отправляет историю сообщений к Anthropic Claude и транслирует ответ в реальном времени.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        yield "Ошибка: не найден ANTHROPIC_API_KEY в .env"
        return

    client = Anthropic(api_key=api_key)

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
        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as e:
        yield f"\n[Ошибка генерации Anthropic: {str(e)}]"


def list_available_anthropic_models() -> List[str]:
    """
    Получает список доступных моделей от Anthropic API.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return []
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        # Проверяем наличие метода list
        if hasattr(client, 'models') and hasattr(client.models, 'list'):
            models_list = client.models.list()
            return [m.id for m in models_list.data]
        return []
    except Exception:
        return []
