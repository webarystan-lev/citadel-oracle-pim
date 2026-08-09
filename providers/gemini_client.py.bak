import os
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Generator, List, Dict

# Загружаем ключи из .env
load_dotenv()

def ask_gemini(prompt: str, model_name: str = "gemini-2.5-flash") -> str:
    """
    Отправляет запрос к Google Gemini и возвращает ответ (синхронно).
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Ошибка: не найден GEMINI_API_KEY в .env"

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)

    return response.text


def stream_gemini(messages: List[Dict[str, str]], model_name: str, temperature: float, max_tokens: int) -> Generator[str, None, None]:
    """
    Отправляет историю сообщений к Google Gemini и транслирует ответ в реальном времени.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        yield "Ошибка: не найден GEMINI_API_KEY в .env"
        return

    genai.configure(api_key=api_key)

    contents = []
    system_instruction = None
    for msg in messages:
        if msg["role"] == "system":
            system_instruction = msg["content"]
        else:
            contents.append({
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [msg["content"]]
            })

    generation_config = genai.types.GenerationConfig(
        temperature=temperature,
        max_output_tokens=max_tokens
    )

    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            system_instruction=system_instruction
        )
        response = model.generate_content(contents, stream=True)
        for chunk in response:
            try:
                if chunk.text:
                    yield chunk.text
            except Exception:
                pass
    except Exception as e:
        yield f"\n[Ошибка генерации Gemini: {str(e)}]"


def list_available_gemini_models() -> List[str]:
    """
    Получает список доступных моделей от Google Gemini API.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return []
    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        return [m.name.replace("models/", "") for m in models if "generateContent" in m.supported_generation_methods]
    except Exception:
        return []
