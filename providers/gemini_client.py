# providers/gemini_client.py
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from typing import Generator, List, Dict, Optional

load_dotenv()

def ask_gemini(prompt: str, model_name: str = "gemini-2.5-flash") -> str:
    """
    Отправляет запрос к Google Gemini и возвращает ответ (синхронно).
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Ошибка: не найден GEMINI_API_KEY в .env"

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"Ошибка генерации Gemini: {str(e)}"

# Псевдоним для совместимости
generate_gemini_content = ask_gemini


def stream_gemini(
    messages: List[Dict[str, str]], 
    model_name: str = "gemini-2.5-flash", 
    temperature: float = 0.7, 
    max_tokens: int = 4096,
    system_prompt: Optional[str] = None
) -> Generator[str, None, None]:
    """
    Отправляет историю сообщений к Google Gemini и транслирует ответ в реальном времени.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        yield "Ошибка: не найден GEMINI_API_KEY в .env"
        return

    contents = []
    system_instruction = system_prompt
    
    for msg in messages:
        if msg["role"] == "system":
            system_instruction = msg["content"]
        else:
            contents.append({
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [{"text": msg["content"]}]
            })

    config_args = {
        "temperature": temperature,
        "max_output_tokens": max_tokens,
    }
    
    if system_instruction:
        config_args["system_instruction"] = system_instruction

    generation_config = types.GenerateContentConfig(**config_args)

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content_stream(
            model=model_name,
            contents=contents,
            config=generation_config
        )
        for chunk in response:
            try:
                if chunk.text:
                    yield chunk.text
            except Exception:
                pass
    except Exception as e:
        yield f"\n[Ошибка генерации Gemini: {str(e)}]"

# Псевдоним для совместимости
stream_gemini_response = stream_gemini


def list_available_gemini_models() -> List[str]:
    """
    Получает список доступных моделей от Google Gemini API.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return []
    try:
        client = genai.Client(api_key=api_key)
        models = client.models.list()
        res = []
        for m in models:
            actions = getattr(m, 'supported_actions', None) or getattr(m, 'supported_generation_methods', None) or []
            if "generateContent" in actions:
                res.append(m.name.replace("models/", ""))
        return res
    except Exception:
        return []
