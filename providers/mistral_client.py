import os
from mistralai.client import Mistral
from dotenv import load_dotenv
from typing import Generator, List, Dict

# Загружаем ключи из .env
load_dotenv()

def ask_mistral(prompt: str, model_name: str = "mistral-large-latest") -> str:
    """
    Отправляет запрос к Mistral AI и возвращает ответ (синхронно).
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return "Ошибка: не найден MISTRAL_API_KEY в .env"

    client = Mistral(api_key=api_key)

    response = client.chat.complete(
        model=model_name,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


def stream_mistral(messages: List[Dict[str, str]], model_name: str, temperature: float, max_tokens: int) -> Generator[str, None, None]:
    """
    Отправляет историю сообщений к Mistral AI и транслирует ответ в реальном времени.
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        yield "Ошибка: не найден MISTRAL_API_KEY в .env"
        return

    client = Mistral(api_key=api_key)

    api_messages = []
    for msg in messages:
        # Убедимся, что формат сообщений соответствует ожидаемому Mistral API
        api_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    try:
        response = client.chat.stream(
            model=model_name,
            messages=api_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        for chunk in response:
            delta = None
            if hasattr(chunk, 'data') and hasattr(chunk.data, 'choices') and chunk.data.choices:
                delta = chunk.data.choices[0].delta.content
            elif hasattr(chunk, 'choices') and chunk.choices:
                delta = chunk.choices[0].delta.content
                
            if delta is not None:
                yield delta
    except Exception as e:
        yield f"\n[Ошибка генерации Mistral: {str(e)}]"


def list_available_mistral_models() -> List[str]:
    """
    Получает список доступных моделей от Mistral API.
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return []
    try:
        from mistralai.client import Mistral
        client = Mistral(api_key=api_key)
        models_list = client.models.list()
        return [m.id for m in models_list.data]
    except Exception:
        return []
