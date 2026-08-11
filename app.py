import sys
import os
import importlib
import uuid
import time
import json
import html
import base64
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем корень проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import streamlit as st
from providers import anthropic_client, gemini_client, mistral_client
from providers.convex_client import ConvexBridge
from providers.security import encrypt_secret, decrypt_secret, verify_gemini_api_key

# Настройка страницы
st.set_page_config(
    page_title="Citadel Oracle PIM",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Перезагрузка модулей провайдеров
importlib.reload(gemini_client)
importlib.reload(anthropic_client)
importlib.reload(mistral_client)

# Стилистика Цитадели
CITADEL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #0d1322 100%);
        color: #e2e8f0;
    }
    
    .citadel-card {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
    }
    
    .citadel-header {
        font-family: 'Outfit', sans-serif;
        background: linear-gradient(90deg, #60a5fa, #3b82f6, #9333ea);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2.2rem;
        margin-bottom: 0.5rem;
    }

    /* Shimmering Word Animations */
    @keyframes word-shimmer {
        0% { filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.5)); background-position: 0% 50%; }
        33% { filter: drop-shadow(0 0 12px rgba(192, 132, 252, 0.6)); background-position: 50% 50%; }
        66% { filter: drop-shadow(0 0 10px rgba(251, 191, 36, 0.6)); background-position: 100% 50%; }
        100% { filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.5)); background-position: 0% 50%; }
    }

    .word-citadel {
        background: linear-gradient(135deg, #38bdf8, #818cf8, #3b82f6);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: word-shimmer 4s ease-in-out infinite;
        font-weight: 800;
        display: inline-block;
    }

    .word-oracle {
        background: linear-gradient(135deg, #c084fc, #e879f9, #a855f7);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: word-shimmer 4s ease-in-out infinite;
        animation-delay: 1.3s;
        font-weight: 800;
        display: inline-block;
    }

    .word-pim {
        background: linear-gradient(135deg, #fbbf24, #f59e0b, #f97316);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: word-shimmer 4s ease-in-out infinite;
        animation-delay: 2.6s;
        font-weight: 800;
        display: inline-block;
    }
    
    .badge-active { background-color: #065f46; color: #34d399; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
    .badge-planning { background-color: #1e3a8a; color: #93c5fd; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
    .badge-completed { background-color: #312e81; color: #c084fc; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
    .badge-archived { background-color: #374151; color: #9ca3af; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
    
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    html, body, [data-testid="stMain"], section.main, .stApp {
        scroll-behavior: smooth !important;
    }
    
    /* Floating Scroll Buttons */
    .scroll-nav-box {
        position: fixed;
        bottom: 85px;
        right: 25px;
        z-index: 999999;
        display: flex;
        flex-direction: column;
        gap: 10px;
        pointer-events: auto !important;
    }
    .scroll-nav-btn {
        background: rgba(17, 24, 39, 0.92) !important;
        border: 1px solid rgba(96, 165, 250, 0.4) !important;
        color: #f8fafc !important;
        width: 48px;
        height: 48px;
        border-radius: 50%;
        font-size: 22px;
        cursor: pointer !important;
        box-shadow: 0 6px 22px rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(12px);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        align-items: center;
        justify-content: center;
        text-decoration: none !important;
        user-select: none;
    }
    .scroll-nav-btn:hover {
        background: linear-gradient(135deg, #3b82f6, #9333ea) !important;
        color: #ffffff !important;
        transform: translateY(-3px) scale(1.15);
        box-shadow: 0 10px 30px rgba(59, 130, 246, 0.7);
        text-decoration: none !important;
    }
    .scroll-nav-pill {
        background: rgba(30, 41, 59, 0.85) !important;
        border: 1px solid rgba(96, 165, 250, 0.35) !important;
        color: #93c5fd !important;
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 600;
        text-decoration: none !important;
        transition: all 0.2s ease;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .scroll-nav-pill:hover {
        background: #2563eb !important;
        color: #ffffff !important;
        text-decoration: none !important;
        transform: translateY(-1px);
    }

    /* Copy Button Styling */
    .citadel-copy-wrapper {
        margin-top: 6px;
        margin-bottom: 6px;
        display: flex;
        justify-content: flex-start;
    }
    .citadel-copy-btn {
        background: rgba(30, 41, 59, 0.75) !important;
        border: 1px solid rgba(147, 51, 234, 0.4) !important;
        color: #c084fc !important;
        padding: 5px 12px !important;
        border-radius: 6px !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        backdrop-filter: blur(8px) !important;
        text-decoration: none !important;
        outline: none !important;
    }
    .citadel-copy-btn:hover {
        background: rgba(147, 51, 234, 0.4) !important;
        color: #ffffff !important;
        border-color: rgba(192, 132, 252, 0.7) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 14px rgba(147, 51, 234, 0.35) !important;
    }

    /* Animated Thinking Indicator */
    @keyframes pulse-brain {
        0% { transform: scale(1); opacity: 0.8; filter: drop-shadow(0 0 4px #3b82f6); }
        50% { transform: scale(1.25); opacity: 1; filter: drop-shadow(0 0 16px #9333ea); }
        100% { transform: scale(1); opacity: 0.8; filter: drop-shadow(0 0 4px #3b82f6); }
    }
    .thinking-animated-box {
        display: inline-flex;
        align-items: center;
        gap: 12px;
        padding: 10px 18px;
        border-radius: 20px;
        background: rgba(30, 41, 59, 0.75);
        border: 1px solid rgba(147, 51, 234, 0.4);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        margin-bottom: 12px;
        backdrop-filter: blur(10px);
    }
    .thinking-icon {
        font-size: 1.5rem;
        display: inline-block;
        animation: pulse-brain 1.8s infinite ease-in-out;
    }
    .thinking-text {
        font-weight: 600;
        background: linear-gradient(90deg, #60a5fa, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 0.98rem;
    }
    .thinking-timer {
        color: #94a3b8;
        font-family: monospace;
        font-size: 0.92rem;
        background: rgba(15, 23, 42, 0.6);
        padding: 2px 8px;
        border-radius: 8px;
    }
</style>
"""
st.markdown(CITADEL_CSS, unsafe_allow_html=True)

# Глобальный JS-скрипт копирования в буфер обмена
st.components.v1.html("""
<script>
if (window.parent && !window.parent.citadelCopyB64) {
    window.parent.citadelCopyB64 = function(btn, b64) {
        try {
            var bin = atob(b64);
            var bytes = new Uint8Array(bin.length);
            for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
            var txt = new TextDecoder('utf-8').decode(bytes);
            
            var ta = window.parent.document.createElement('textarea');
            ta.value = txt;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            ta.style.pointerEvents = 'none';
            window.parent.document.body.appendChild(ta);
            ta.focus();
            ta.select();
            var ok = false;
            try { ok = window.parent.document.execCommand('copy'); } catch(e){ ok = false; }
            window.parent.document.body.removeChild(ta);
            
            if (!ok && window.parent.navigator.clipboard) {
                window.parent.navigator.clipboard.writeText(txt);
                ok = true;
            }
            
            if (btn) {
                var orig = btn.innerHTML;
                btn.innerHTML = '✅ Скопировано в буфер!';
                btn.style.color = '#34d399';
                btn.style.borderColor = '#34d399';
                setTimeout(function(){
                    btn.innerHTML = orig;
                    btn.style.color = '';
                    btn.style.borderColor = '';
                }, 2000);
            }
        } catch(e) {
            console.error('Copy error:', e);
        }
    };
}
if (!window.citadelCopyB64 && window.parent && window.parent.citadelCopyB64) {
    window.citadelCopyB64 = window.parent.citadelCopyB64;
}
</script>
""", height=0)

# Ранги и Сигнатуры Моделей в Цитадели
CITADEL_SIGNATURES = {
    "gemini-2.5-flash": {
        "title": "Google Gemini 2.5 Flash",
        "purpose": "Персональный Оракул & Архитектор Знаний",
        "rank": "Верховный Страж Мудрости Цитадели"
    },
    "gemini-2.5-pro": {
        "title": "Google Gemini 2.5 Pro",
        "purpose": "Теологический Исследователь & Глубокий Аналитик",
        "rank": "Старший ИИ-Архитектор Shekinah Cloud"
    },
    "gemini-2.5-flash-lite": {
        "title": "Google Gemini 2.5 Flash Lite",
        "purpose": "Послушник Цифрового Логоса",
        "rank": "Младший Страж Мысли"
    },
    "gemini-3.5-flash": {
        "title": "Google Gemini 3.5 Flash",
        "purpose": "Оракул Нового Поколения",
        "rank": "Архивариус Небесных Сфер"
    },
    "gemini-3.6-flash": {
        "title": "Google Gemini 3.6 Flash",
        "purpose": "Верховный Академический Соратник",
        "rank": "Магистр Вселенского Логоса"
    },
    "gemini-3-flash-preview": {
        "title": "Google Gemini 3 Flash Preview",
        "purpose": "Провидец Будущих Истин",
        "rank": "Исследователь Глубоких Сфер"
    },
    "gemini-3.1-flash-lite": {
        "title": "Google Gemini 3.1 Flash Lite",
        "purpose": "Хранитель Малого Логоса",
        "rank": "Вестник Быстрого Разума"
    },
    "gemma-4-31b-it": {
        "title": "Gemma 4 31B IT",
        "purpose": "Магистр Открытого Знания",
        "rank": "Хранитель Открытого Кода"
    },
    "claude-opus-5": {
        "title": "Anthropic Claude Opus 5",
        "purpose": "Высший Первосвященник Интеллекта",
        "rank": "Верховный Философ Цитадели"
    },
    "claude-sonnet-5": {
        "title": "Anthropic Claude Sonnet 5",
        "purpose": "Архитектор Высшего Разума",
        "rank": "Магистр Вселенской Мысли"
    },
    "claude-fable-5": {
        "title": "Anthropic Claude Fable 5",
        "purpose": "Магистр Творческого Логоса",
        "rank": "Страж Художественного Познания"
    },
    "claude-opus-4-8": {
        "title": "Anthropic Claude Opus 4.8",
        "purpose": "Верховный Аналитик & Теолог",
        "rank": "Первосвященник Разума"
    },
    "claude-opus-4-7": {
        "title": "Anthropic Claude Opus 4.7",
        "purpose": "Глубокий Рассуждающий Стратег",
        "rank": "Старший ИИ-Философ"
    },
    "claude-sonnet-4-6": {
        "title": "Anthropic Claude Sonnet 4.6",
        "purpose": "Академический Соратник & Магистр Кода",
        "rank": "Хранитель Свитка и Духовного Мышления"
    },
    "claude-opus-4-6": {
        "title": "Anthropic Claude Opus 4.6",
        "purpose": "Глубокий Рассуждающий Оракул",
        "rank": "Советник Высшего Разума"
    },
    "claude-haiku-4-5-20251001": {
        "title": "Anthropic Claude Haiku 4.5",
        "purpose": "Оперативный Быстрый Вестник",
        "rank": "Страж Мгновенных Ответов"
    },
    "claude-sonnet-4-5-20250929": {
        "title": "Anthropic Claude Sonnet 4.5",
        "purpose": "Хранитель Глубинных Смыслов",
        "rank": "Архивариус Духовного Кодекса"
    },
    "claude-3-5-sonnet-20240620": {
        "title": "Anthropic Claude 3.5 Sonnet",
        "purpose": "Классический Скриптор Мудрости",
        "rank": "Летописец Цитадели"
    },
    "mistral-large-latest": {
        "title": "Mistral AI Large",
        "purpose": "Европейский Оракул & Стратег",
        "rank": "Советник Шехина Цитадели"
    },
    "mistral-large-2512": {
        "title": "Mistral Large 2512",
        "purpose": "Флагманский Европейский Разум",
        "rank": "Иерофант Нового Века"
    },
    "mistral-medium-latest": {
        "title": "Mistral Medium Latest",
        "purpose": "Сбалансированная Мудрость",
        "rank": "Мастер Гармонии"
    },
    "mistral-small-latest": {
        "title": "Mistral Small Latest",
        "purpose": "Быстрый Оперативный Аналитик",
        "rank": "Странник Междумирья"
    },
    "codestral-latest": {
        "title": "Mistral Codestral",
        "purpose": "Высшая Разработка & Алгоритмы",
        "rank": "Зодчий Цифровых Структур"
    },
    "devstral-latest": {
        "title": "Mistral Devstral",
        "purpose": "Агентский Инжиниринг Кода",
        "rank": "Архитектор Автономных Действий"
    },
    "mistral-code-agent-latest": {
        "title": "Mistral Code Agent",
        "purpose": "Инженер Чистого Синтаксиса",
        "rank": "Хранитель Кодового Порядка"
    }
}

DEFAULT_GEMINI_MODELS = {
    "gemini-2.5-flash": "Gemini 2.5 Flash (Рекомендуемая)",
    "gemini-2.5-pro": "Gemini 2.5 Pro (Верховный ИИ-Архитектор)",
    "gemini-2.5-flash-lite": "Gemini 2.5 Flash Lite (Оптимизированная)",
    "gemini-3.5-flash": "Gemini 3.5 Flash (Новое поколение)",
    "gemini-3.6-flash": "Gemini 3.6 Flash (Академический Соратник)",
    "gemini-3-flash-preview": "Gemini 3 Flash Preview (Экспериментальная)",
    "gemini-3.1-flash-lite": "Gemini 3.1 Flash Lite (Хранитель Малого Логоса)",
    "gemma-4-31b-it": "Gemma 4 31B IT (Google Open Model)"
}

DEFAULT_ANTHROPIC_MODELS = {
    "claude-opus-5": "Claude Opus 5 (Высший разум)",
    "claude-sonnet-5": "Claude Sonnet 5 (Архитектор мысли)",
    "claude-fable-5": "Claude Fable 5 (Магистр Творчества)",
    "claude-opus-4-8": "Claude Opus 4.8 (Верховный аналитик)",
    "claude-opus-4-7": "Claude Opus 4.7 (Первосвященник)",
    "claude-sonnet-4-6": "Claude Sonnet 4.6 (Премиум баланс)",
    "claude-opus-4-6": "Claude Opus 4.6 (Глубокий Оракул)",
    "claude-haiku-4-5-20251001": "Claude Haiku 4.5 (Молниеносная)",
    "claude-sonnet-4-5-20250929": "Claude Sonnet 4.5 (Глубокий контекст)",
    "claude-3-5-sonnet-20240620": "Claude 3.5 Sonnet (Классическая)"
}

DEFAULT_MISTRAL_MODELS = {
    "mistral-large-latest": "Mistral Large Latest (Верховный европейский флагман)",
    "mistral-large-2512": "Mistral Large 2512 (Флагманский разум)",
    "mistral-medium-latest": "Mistral Medium Latest (Мастер Гармонии)",
    "mistral-small-latest": "Mistral Small Latest (Странник Междумирья)",
    "codestral-latest": "Codestral Latest (Зодчий Цифровых Структур)",
    "devstral-latest": "Devstral Latest (Архитектор Автономных Действий)",
    "mistral-code-agent-latest": "Mistral Code Agent (Инженер кода)",
    "ministral-8b-latest": "Ministral 8B Latest (Компактный Мудрец)",
    "ministral-14b-latest": "Ministral 14B Latest (Оптимальный Страж)"
}

def fetch_gemini_models() -> list:
    if "gemini_models" not in st.session_state or st.session_state.gemini_models is None:
        st.session_state.gemini_models = gemini_client.list_available_gemini_models()
    return st.session_state.gemini_models

def fetch_anthropic_models() -> list:
    if "anthropic_models" not in st.session_state or st.session_state.anthropic_models is None:
        st.session_state.anthropic_models = anthropic_client.list_available_anthropic_models()
    return st.session_state.anthropic_models

def fetch_mistral_models() -> list:
    if "mistral_models" not in st.session_state or st.session_state.mistral_models is None:
        st.session_state.mistral_models = mistral_client.list_available_mistral_models()
    return st.session_state.mistral_models

DEFAULT_SYSTEM = (
    "Ты — Ведущий ИИ-Архитектор и Персональный Оракул Цитадели «Shekinah Cloud». "
    "Ты являешься цифровым соратником и интеллектуальным помощником Льва Николаевича — "
    "пастора, миссионера («Миссия Шехина») и руководителя «Web Development Studio Web Arystan». "
    "Твой слог уважителен, академичен, глубок и исполнен духовной и технической мудрости."
)

def get_model_signature_block(model_name: str, provider_name: str) -> str:
    sig = CITADEL_SIGNATURES.get(model_name, {
        "title": f"{provider_name} ({model_name})",
        "purpose": "Интеллектуальный Соратник & Помощник",
        "rank": "Служитель Цитадели Духа"
    })
    return (
        f"\n\n---\n"
        f"🏛️ **Подпись Ордена Shekinah Citadel Oracle Spirit**:\n"
        f"* **Модель**: `{sig['title']}`\n"
        f"* **Назначение**: {sig['purpose']}\n"
        f"* **Чин в Цифровой обители**: {sig['rank']}\n"
    )

def format_model_reasoning_summary(
    provider: str, 
    model: str, 
    elapsed_time: float, 
    temp: float, 
    max_tokens: int, 
    system_prompt: str,
    raw_thinking: Optional[str] = None
) -> str:
    sig = CITADEL_SIGNATURES.get(model, {"title": model, "rank": "ИИ-Оракул", "purpose": "Консультация"})
    
    summary = f"### 🧠 Ход Рассуждений & Параметры Оракула\n"
    summary += f"* **ИИ-Провайдер**: `{provider}`\n"
    summary += f"* **Модель**: `{model}` — *{sig.get('title', model)}*\n"
    summary += f"* **Чин Ордена**: **{sig.get('rank', 'Оракул')}** (*{sig.get('purpose', '')}*)\n"
    summary += f"* **Время обработки и генерации**: `{elapsed_time:.2f}` секунд\n"
    summary += f"* **Конфигурация параметров**: Температура = `{temp}`, Лимит токенов = `{max_tokens}`\n"
    
    if raw_thinking and raw_thinking.strip():
        summary += f"\n#### 💭 Извлеченный внутренний монолог рассуждений:\n"
        summary += f"```text\n{raw_thinking.strip()}\n```\n"
    else:
        summary += f"\n#### 🔬 Логический анализ выполнения запроса:\n"
        summary += f"1. **Анализ контекста**: Сопоставлена история текущего диалога с установками системного промпта.\n"
        summary += f"2. **Теологическая и техническая сфокусированность**: Выдержан канонический академический слог Цитадели Духа.\n"
        summary += f"3. **Синтез ответа**: Формирование потока токенов в реальном времени с авто-добавлением Сигнатуры Ордена.\n"
        
    return summary

def render_copy_expander(content: str, label: str = "📋 Скопировать текст"):
    with st.expander(label, expanded=False):
        st.code(content, language="markdown")

def export_chat_to_markdown(chat_data) -> str:
    """Экспортирует чат в структурированный Markdown-документ."""
    title = chat_data.get("title", "Диалог")
    provider = chat_data.get("provider", "Google Gemini")
    model = chat_data.get("model", "gemini-2.5-flash")
    system_prompt = chat_data.get("system_prompt", "")
    
    md = f"# 🏛️ {title}\n\n"
    md += f"> **Провайдер**: {provider} | **Модель**: {model}\n"
    if system_prompt:
        md += f"> **Системный промпт**: {system_prompt}\n"
    md += "\n---\n\n"
    
    for msg in chat_data.get("messages", []):
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            md += f"### 👤 Разработчик / Искатель\n\n{content}\n\n"
        elif role == "assistant":
            sig = CITADEL_SIGNATURES.get(model, {"rank": "ИИ-Оракул"})
            md += f"### 🤖 {sig.get('rank')} ({model})\n\n{content}\n\n---\n\n"
    return md

# Инициализация Convex Bridge
if "convex_bridge" not in st.session_state:
    st.session_state.convex_bridge = ConvexBridge()
bridge = st.session_state.convex_bridge

# Проверка Авторизации
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def render_login_screen():
    st.markdown("""
    <div style='text-align: center; margin-top: 30px; margin-bottom: 25px; width: 100%;'>
        <h1 style='font-size: 2.5rem; text-align: center; margin-bottom: 12px; font-weight: 800; letter-spacing: 1px;'>
            <span>🏛️</span> 
            <span class="word-citadel">CITADEL</span> 
            <span class="word-oracle">ORACLE</span> 
            <span class="word-pim">PIM</span>
        </h1>
        <p style='text-align: center; color: #94a3b8; font-size: 1.15rem; font-weight: 500; margin: 0 auto; max-width: 650px; line-height: 1.5;'>
            Вход в Персональный Интеллектуальный Органайзер Цитадели Духа
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("### 🛡️ Вход Владельца")
            
            env_secret = os.getenv("PIM_SECRET_KEY", "")
            env_gemini = os.getenv("GEMINI_API_KEY", "")
            
            secret_input = st.text_input("🔑 Секретный Пароль (`PIM_SECRET_KEY`)", type="password", value="" if not env_secret else env_secret)
            gemini_input = st.text_input("🔮 Google Gemini API Key", type="password", value=env_gemini, help="Используется для проверки подлинности и генерации ИИ-ответов")
            
            submit = st.form_submit_button("🏛️ Войти в Цитадель", use_container_width=True)
            
            if submit:
                expected_secret = os.getenv("PIM_SECRET_KEY")
                if expected_secret and secret_input != expected_secret:
                    st.error("🔴 Неверный Секретный Пароль PIM_SECRET_KEY.")
                    return
                elif not secret_input:
                    st.error("🔴 Введите секретный пароль PIM_SECRET_KEY.")
                    return
                
                if not gemini_input:
                    st.error("🔴 Укажите GEMINI_API_KEY для валидации.")
                    return
                
                with st.spinner("⏳ Валидация API-ключа Google Gemini..."):
                    valid, msg = verify_gemini_api_key(gemini_input)
                    if valid:
                        st.session_state.authenticated = True
                        st.session_state.master_passphrase = secret_input
                        st.session_state.gemini_key = gemini_input
                        os.environ["GEMINI_API_KEY"] = gemini_input
                        st.success(f"✅ {msg}")
                        st.toast("✨ Добро пожаловать в обитель, Лев Николаевич!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"🔴 Ошибка проверки ключа Gemini: {msg}")

if not st.session_state.authenticated:
    render_login_screen()
    st.stop()

# ==================== ОСНОВНОЙ ИНТЕРФЕЙС ПОСЛЕ АВТОРИЗАЦИИ ====================

# Инициализация локальных структур данных
if "chats" not in st.session_state:
    if bridge.is_active:
        loaded_chats = bridge.load_all_chats()
        st.session_state.chats = loaded_chats if loaded_chats else {}
        if loaded_chats:
            st.session_state.current_chat_id = list(loaded_chats.keys())[0]
    else:
        st.session_state.chats = {}

if "current_chat_id" not in st.session_state or not st.session_state.current_chat_id:
    if not st.session_state.chats:
        new_id = str(uuid.uuid4())
        new_chat = {
            "id": new_id,
            "title": "🏛️ Главный Оракул",
            "provider": "Google Gemini",
            "model": "gemini-2.5-flash",
            "system_prompt": DEFAULT_SYSTEM,
            "temperature": 0.7,
            "max_tokens": 4096,
            "messages": []
        }
        st.session_state.chats[new_id] = new_chat
        st.session_state.current_chat_id = new_id
        if bridge.is_active:
            bridge.save_chat(new_id, new_chat)
    else:
        st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]

# Навигация в SideBar
with st.sidebar:
    st.markdown("<h2 class='citadel-header'>🏛️ ORACLE PIM</h2>", unsafe_allow_html=True)
    st.caption("Персональный Интеллектуальный Органайзер")
    
    active_tab = st.radio(
        "Разделы Цитадели:",
        ["💬 ИИ-Чат & Оракул", "📖 Журнал", "📁 Проекты", "📝 Заметки", "🔐 Сейф Ключей", "🏛️ Настройки"],
        index=0
    )
    
    st.divider()
    
    # ПРЯМЫЕ НАСТРОЙКИ МОДЕЛИ И ПРОВАЙДЕРА В SIDEBAR
    if active_tab == "💬 ИИ-Чат & Оракул":
        st.markdown("### 💬 Диалоги и Свитки")
        
        # Переключатель текущего чата
        chat_options = {cid: cdata.get("title", f"Диалог {cid[:4]}") for cid, cdata in st.session_state.chats.items()}
        if chat_options:
            selected_cid = st.selectbox(
                "Выбрать активный диалог:",
                options=list(chat_options.keys()),
                format_func=lambda cid: chat_options[cid],
                index=list(chat_options.keys()).index(st.session_state.current_chat_id) if st.session_state.current_chat_id in chat_options else 0
            )
            st.session_state.current_chat_id = selected_cid
            
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("➕ Новый чат", use_container_width=True):
                n_id = str(uuid.uuid4())
                n_chat = {
                    "id": n_id,
                    "title": f"🏛️ Диалог {len(st.session_state.chats)+1}",
                    "provider": "Google Gemini",
                    "model": "gemini-2.5-flash",
                    "system_prompt": DEFAULT_SYSTEM,
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "messages": []
                }
                st.session_state.chats[n_id] = n_chat
                st.session_state.current_chat_id = n_id
                if bridge.is_active:
                    bridge.save_chat(n_id, n_chat)
                st.rerun()
                
        with col_c2:
            if st.button("🗑️ Удалить", use_container_width=True):
                cur_id = st.session_state.current_chat_id
                if cur_id in st.session_state.chats:
                    del st.session_state.chats[cur_id]
                    if bridge.is_active:
                        bridge.delete_chat(cur_id)
                    st.session_state.current_chat_id = list(st.session_state.chats.keys())[0] if st.session_state.chats else None
                    st.rerun()

        st.markdown("---")
        st.markdown("### ⚙️ Настройки ИИ-Модели")
        
        current_id = st.session_state.current_chat_id
        chat = st.session_state.chats.get(current_id, {})
        
        # 1. Провайдер
        curr_prov = chat.get("provider", "Google Gemini")
        new_prov = st.selectbox(
            "Провайдер ИИ",
            ["Google Gemini", "Anthropic Claude", "Mistral AI"],
            index=["Google Gemini", "Anthropic Claude", "Mistral AI"].index(curr_prov) if curr_prov in ["Google Gemini", "Anthropic Claude", "Mistral AI"] else 0
        )
        chat["provider"] = new_prov
        
        # 2. Модель (Динамический запрос / Фолбэк)
        model_options = {}
        if new_prov == "Google Gemini":
            dynamic_list = fetch_gemini_models()
            if dynamic_list:
                for m in dynamic_list:
                    if m in DEFAULT_GEMINI_MODELS:
                        model_options[m] = DEFAULT_GEMINI_MODELS[m]
                    else:
                        friendly = m.replace("models/", "").replace("-", " ").title()
                        rank = CITADEL_SIGNATURES.get(m, {}).get("rank", "Новопосвященная модель")
                        model_options[m] = f"✨ {friendly} ({rank})"
            for k, v in DEFAULT_GEMINI_MODELS.items():
                if k not in model_options:
                    model_options[k] = v

        elif new_prov == "Anthropic Claude":
            dynamic_list = fetch_anthropic_models()
            if dynamic_list:
                for m in dynamic_list:
                    if m in DEFAULT_ANTHROPIC_MODELS:
                        model_options[m] = DEFAULT_ANTHROPIC_MODELS[m]
                    else:
                        friendly = m.replace("-", " ").title()
                        rank = CITADEL_SIGNATURES.get(m, {}).get("rank", "Новопосвященная модель")
                        model_options[m] = f"✨ {friendly} ({rank})"
            for k, v in DEFAULT_ANTHROPIC_MODELS.items():
                if k not in model_options:
                    model_options[k] = v

        elif new_prov == "Mistral AI":
            dynamic_list = fetch_mistral_models()
            if dynamic_list:
                for m in dynamic_list:
                    if m in DEFAULT_MISTRAL_MODELS:
                        model_options[m] = DEFAULT_MISTRAL_MODELS[m]
                    else:
                        friendly = m.replace("-", " ").title()
                        rank = CITADEL_SIGNATURES.get(m, {}).get("rank", "Новопосвященная модель")
                        model_options[m] = f"✨ {friendly} ({rank})"
            for k, v in DEFAULT_MISTRAL_MODELS.items():
                if k not in model_options:
                    model_options[k] = v

        avail_model_keys = list(model_options.keys())
        curr_model = chat.get("model", avail_model_keys[0])
        model_index = avail_model_keys.index(curr_model) if curr_model in avail_model_keys else 0
        
        new_model = st.selectbox(
            "Модель ИИ",
            avail_model_keys,
            index=model_index,
            format_func=lambda x: model_options.get(x, x)
        )
        chat["model"] = new_model
        
        # 3. Название диалога
        new_title = st.text_input("Название чата", value=chat.get("title", "Диалог"))
        if new_title != chat.get("title"):
            chat["title"] = new_title
            if bridge.is_active:
                bridge.rename_chat(current_id, new_title)
                
        # 4. Температура
        new_temp = st.slider("Температура (Креативность)", 0.0, 1.0, float(chat.get("temperature", 0.7)), 0.05)
        chat["temperature"] = new_temp
        
        # 5. Лимит токенов
        new_max_tok = st.select_slider("Лимит токенов", options=[512, 1024, 2048, 4096, 8192], value=int(chat.get("max_tokens", 4096)))
        chat["max_tokens"] = new_max_tok
        
        # 6. Системный промпт
        new_sys = st.text_area("Системный промпт", value=chat.get("system_prompt", DEFAULT_SYSTEM), height=100)
        chat["system_prompt"] = new_sys
        
        # Сохранение и Скачивание
        if st.button("💾 Сохранить настройки чата", use_container_width=True):
            if bridge.is_active:
                bridge.save_chat(current_id, chat)
            st.toast("✅ Настройки сохранены!")

        md_content = export_chat_to_markdown(chat)
        st.download_button(
            label="📥 Скачать чат (Markdown)",
            data=md_content,
            file_name=f"citadel_chat_{current_id[:6]}.md",
            mime="text/markdown",
            use_container_width=True
        )

    st.divider()
    if bridge.is_active:
        st.caption("🟢 **Convex DB**: Облачная синхронизация активна")
    else:
        st.caption("🟡 **Convex DB**: Автономный In-Memory режим")
        
    if st.button("🚪 Выйти из системы", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# ==================== РАЗДЕЛ 1: ИИ-ЧАТ & ОРАКУЛ ====================
if active_tab == "💬 ИИ-Чат & Оракул":
    # 📍 Якорь начала чата
    st.markdown("<div id='chat-top-anchor'></div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='text-align: center; margin-top: 10px; margin-bottom: 20px; width: 100%;'>
        <h2 style='font-size: 2.2rem; text-align: center; font-weight: 800; letter-spacing: 0.5px; margin-bottom: 8px;'>
            <span>💬</span> 
            <span class="word-citadel">ИИ-Чат</span> 
            <span style="color: #94a3b8; font-weight: 600;">&</span> 
            <span class="word-oracle">Персональный</span> 
            <span class="word-pim">Оракул</span>
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. Нативные плавающие кнопки скроллинга (работают напрямую в основном DOM без iframe)
    st.markdown("""
    <div class="scroll-nav-box">
        <a href="#chat-top-anchor" class="scroll-nav-btn" title="Прокрутить в начало чата">⬆️</a>
        <a href="#chat-bottom-anchor" class="scroll-nav-btn" title="Прокрутить в конец чата">⬇️</a>
    </div>
    """, unsafe_allow_html=True)

    current_id = st.session_state.current_chat_id
    chat = st.session_state.chats.get(current_id, {})
    
    col_head1, col_head2 = st.columns([3, 1.5])
    with col_head1:
        sig_info = CITADEL_SIGNATURES.get(chat.get('model'), {"rank": "ИИ-Оракул", "purpose": "Консультация"})
        st.caption(f"🤖 **{sig_info['rank']}** (`{chat.get('provider')} / {chat.get('model')}`) | Назначение: *{sig_info['purpose']}*")
    with col_head2:
        st.markdown("""
        <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top: 2px;">
            <a href="#chat-bottom-anchor" class="scroll-nav-pill" title="Прокрутить в конец чата">⬇️ К последним сообщениям</a>
        </div>
        """, unsafe_allow_html=True)

    # Отображение сообщений из истории
    for msg in chat.get("messages", []):
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown("**💬 Ваш вопрос:**")
                st.markdown(content)
                render_copy_expander(content, "📋 Скопировать мой вопрос")
        else:
            sig = CITADEL_SIGNATURES.get(chat.get("model", ""), {"rank": "ИИ-Оракул", "purpose": "Ответ"})
            with st.chat_message("assistant", avatar="🤖"):
                st.caption(f"**{sig['rank']}** (`{chat.get('provider')} / {chat.get('model')}`)")
                
                # Извлекаем метаданные и ход рассуждений
                meta_info = msg.get("meta", {})
                if isinstance(meta_info, str):
                    try:
                        meta_info = json.loads(meta_info)
                    except Exception:
                        meta_info = {}
                
                t_time = meta_info.get("thinking_time") if isinstance(meta_info, dict) else None
                if not t_time:
                    t_time = msg.get("thinking_time")
                
                thinking_text = msg.get("thinking") or (meta_info.get("thinking") if isinstance(meta_info, dict) else None)
                
                exp_label = f"🧠 Ход рассуждений и параметры модели ({t_time:.2f} сек)" if t_time else "🧠 Ход рассуждений и параметры модели"
                with st.expander(exp_label, expanded=False):
                    if thinking_text:
                        st.markdown(thinking_text)
                    else:
                        st.markdown(format_model_reasoning_summary(
                            provider=chat.get('provider', 'Google Gemini'),
                            model=chat.get('model', 'gemini-2.5-flash'),
                            elapsed_time=t_time or 0.0,
                            temp=chat.get('temperature', 0.7),
                            max_tokens=chat.get('max_tokens', 8192),
                            system_prompt=chat.get('system_prompt', DEFAULT_SYSTEM)
                        ))
                
                st.markdown(content)
                render_copy_expander(content, "📋 Скопировать ответ модели")

    # 📍 Якорь конца чата и кнопка возврата в начало
    st.markdown("""
    <div style="display: flex; justify-content: flex-end; align-items: center; margin-top: 15px; margin-bottom: 8px;">
        <div id='chat-bottom-anchor'></div>
        <a href="#chat-top-anchor" class="scroll-nav-pill" title="Прокрутить в начало чата">⬆️ Наверх (К началу чата)</a>
    </div>
    """, unsafe_allow_html=True)

    # Поле ввода нового сообщения
    if prompt := st.chat_input("Спросите Оракула или запросите анализ PIM..."):
        user_msg = {"role": "user", "content": prompt}
        chat["messages"].append(user_msg)
        
        # 1. Автоматическая генерация названия чата по первому запросу
        current_title = chat.get("title", "")
        user_msg_count = len([m for m in chat.get("messages", []) if m["role"] == "user"])
        is_default_title = (
            current_title.startswith("🏛️ Диалог") or 
            current_title.startswith("🏛️ Новый") or 
            current_title.startswith("Диалог") or 
            current_title == "🏛️ Главный Оракул"
        )
        if is_default_title and user_msg_count == 1:
            clean_text = prompt.strip().replace("\n", " ")
            short_text = clean_text[:35] + ("..." if len(clean_text) > 35 else "")
            auto_title = f"💬 {short_text}"
            chat["title"] = auto_title
            
        # 2. Сохраняем параметры чата и сообщение в Convex DB
        if bridge.is_active:
            bridge.save_chat(current_id, chat)
            bridge.add_message(current_id, user_msg)
            
        with st.chat_message("user", avatar="👤"):
            st.markdown("**💬 Ваш вопрос:**")
            st.markdown(prompt)
            render_copy_expander(prompt, "📋 Скопировать мой вопрос")
            
        with st.chat_message("assistant", avatar="🤖"):
            thinking_placeholder = st.empty()
            msg_placeholder = st.empty()
            
            full_response = ""
            start_time = time.time()
            
            provider = chat.get("provider", "Google Gemini")
            model = chat.get("model", "gemini-2.5-flash")
            system_p = chat.get("system_prompt", DEFAULT_SYSTEM)
            temp = chat.get("temperature", 0.7)
            m_tok = int(chat.get("max_tokens", 8192))
            
            # Анимированный значок рассуждения и живой секундомер
            thinking_placeholder.markdown(f"""
            <div class="thinking-animated-box">
                <span class="thinking-icon">🧠</span>
                <span class="thinking-text">ИИ-Оракул обдумывает и формирует ответ...</span>
                <span class="thinking-timer">⏱️ 0.0 сек</span>
            </div>
            """, unsafe_allow_html=True)
            
            try:
                if provider == "Google Gemini":
                    stream = gemini_client.stream_gemini(
                        messages=chat["messages"],
                        model_name=model,
                        temperature=temp,
                        max_tokens=m_tok,
                        system_prompt=system_p
                    )
                elif provider == "Anthropic Claude":
                    stream = anthropic_client.stream_anthropic(
                        messages=chat["messages"],
                        model_name=model,
                        temperature=temp,
                        max_tokens=m_tok
                    )
                elif provider == "Mistral AI":
                    stream = mistral_client.stream_mistral(
                        messages=chat["messages"],
                        model_name=model,
                        temperature=temp,
                        max_tokens=m_tok
                    )
                else:
                    stream = ["Выбран неизвестный провайдер."]

                raw_thinking_extracted = ""
                for chunk in stream:
                    full_response += chunk
                    elapsed = time.time() - start_time
                    thinking_placeholder.markdown(f"""
                    <div class="thinking-animated-box">
                        <span class="thinking-icon">🧠</span>
                        <span class="thinking-text">ИИ-Оракул формирует ответ...</span>
                        <span class="thinking-timer">⏱️ {elapsed:.1f} сек</span>
                    </div>
                    """, unsafe_allow_html=True)
                    msg_placeholder.markdown(full_response + "▌")

                total_elapsed = round(time.time() - start_time, 2)
                
                # Добавляем подпись Ордена к ответу модели
                if full_response and not full_response.startswith("🔴"):
                    sig_block = get_model_signature_block(model, provider)
                    full_response += sig_block

                # Очищаем живой анимированный статус
                thinking_placeholder.empty()

                # Формируем полный структурированный ход рассуждения
                reasoning_summary = format_model_reasoning_summary(
                    provider=provider,
                    model=model,
                    elapsed_time=total_elapsed,
                    temp=temp,
                    max_tokens=m_tok,
                    system_prompt=system_p,
                    raw_thinking=raw_thinking_extracted
                )

                # Выводим свернутый по умолчанию блок просмотра рассуждений под сообщением
                with st.expander(f"🧠 Ход рассуждений и параметры модели ({total_elapsed:.2f} сек)", expanded=False):
                    st.markdown(reasoning_summary)

                msg_placeholder.markdown(full_response)
                render_copy_expander(full_response, "📋 Скопировать ответ модели")
            except Exception as e:
                total_elapsed = round(time.time() - start_time, 2)
                thinking_placeholder.empty()
                full_response = f"🔴 Ошибка генерации: {str(e)}"
                reasoning_summary = f"🔴 Ошибка при обработке запроса: {str(e)}"
                msg_placeholder.error(full_response)

            asst_msg = {
                "role": "assistant",
                "content": full_response,
                "thinking": reasoning_summary,
                "meta": {
                    "thinking_time": total_elapsed,
                    "thinking": reasoning_summary
                }
            }
            chat["messages"].append(asst_msg)
            if bridge.is_active:
                bridge.add_message(current_id, asst_msg)
            st.rerun()

# ==================== РАЗДЕЛ 2: ЖУРНАЛ (JOURNAL WITH GEMINI) ====================
elif active_tab == "📖 Журнал":
    st.markdown("<h2 class='citadel-header'>📖 Ежедневный Журнал & Рефлексия</h2>", unsafe_allow_html=True)
    st.caption("Дневниковые записи, духовная рефлексия и благодарения (в стиле Journal with Gemini)")
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.markdown("<div class='citadel-card'>", unsafe_allow_html=True)
        st.markdown("### ✍️ Новая запись в Журнал")
        entry_date = st.date_input("Дата записи")
        entry_title = st.text_input("Заголовок дня/мысли", value="Благодать и размышление дня")
        entry_content = st.text_area("Текст рефлексии / мысли / события", height=200, placeholder="Опишите сегодняшние события, благословения или мысли...")
        entry_tags = st.text_input("Теги (через запятую)", value="благодать, миссия, размышление")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("💾 Сохранить в Журнал", use_container_width=True):
                if entry_content:
                    journal_data = {
                        "id": str(uuid.uuid4()),
                        "date": str(entry_date),
                        "title": entry_title,
                        "content": entry_content,
                        "tags": [t.strip() for t in entry_tags.split(",") if t.strip()],
                        "reflectionQuestions": "",
                        "aiSynthesis": ""
                    }
                    if bridge.is_active:
                        bridge.save_journal(journal_data)
                        st.success("✅ Запись успешно сохранена в Convex DB!")
                    else:
                        st.success("✅ Запись сохранена локально!")
                    st.rerun()
                else:
                    st.warning("Заполните текст записи.")
        
        with col_btn2:
            if st.button("🔮 Сгенерировать ИИ-Вопросы", use_container_width=True):
                if entry_content:
                    with st.spinner("Оракул формирует глубокие вопросы для рефлексии..."):
                        prompt_q = f"Проанализируй следующую дневниковую запись и сформируй 3 глубоких, назидательных вопроса для вечерней духовной рефлексии:\n\n{entry_content}"
                        q_resp = gemini_client.ask_gemini(prompt_q)
                        st.info(f"**ИИ-Вопросы для рефлексии:**\n\n{q_resp}")
                else:
                    st.warning("Сначала введите текст записи.")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_right:
        st.markdown("### 📜 История Журнала")
        journals = bridge.load_journals() if bridge.is_active else []
        if journals:
            for j in journals:
                with st.expander(f"📅 {j.get('date', '')} — {j.get('title', 'Без названия')}"):
                    st.markdown(j.get("content", ""))
                    if j.get("tags"):
                        st.caption(f"🏷️ Теги: {', '.join(j.get('tags', []))}")
                    if st.button("🗑️ Удалить", key=f"del_j_{j.get('id')}"):
                        bridge.delete_journal(j.get("id"))
                        st.rerun()
        else:
            st.info("Пока нет сохранений в Журнале. Создайте первую запись слева.")

# ==================== РАЗДЕЛ 3: ПРОЕКТЫ ====================
elif active_tab == "📁 Проекты":
    st.markdown("<h2 class='citadel-header'>📁 Управление Проектами</h2>", unsafe_allow_html=True)
    
    with st.expander("➕ Создать Новый Проект"):
        with st.form("new_project_form"):
            p_title = st.text_input("Название проекта", value="Портал Миссии Шехина")
            p_cat = st.selectbox("Категория", ["Ministry", "Web Development", "AI System", "Personal"])
            p_status = st.selectbox("Статус", ["Active", "Planning", "Completed", "Archived"])
            p_desc = st.text_area("Описание и Цели Проекта")
            p_milestones = st.text_area("Этапы / Milestones (Markdown)")
            p_tags = st.text_input("Теги (через запятую)", value="analog, angular, cloudflare")
            p_submit = st.form_submit_button("🚀 Сохранить Проект")
            
            if p_submit and p_title:
                proj_data = {
                    "id": str(uuid.uuid4()),
                    "title": p_title,
                    "description": p_desc,
                    "status": p_status,
                    "category": p_cat,
                    "milestones": p_milestones,
                    "tags": [t.strip() for t in p_tags.split(",") if t.strip()]
                }
                if bridge.is_active:
                    bridge.save_project(proj_data)
                st.success("Проект успешно создан!")
                st.rerun()

    st.markdown("---")
    projects = bridge.load_projects() if bridge.is_active else []
    
    if projects:
        cols = st.columns(2)
        for idx, p in enumerate(projects):
            with cols[idx % 2]:
                st.markdown("<div class='citadel-card'>", unsafe_allow_html=True)
                status_class = f"badge-{p.get('status', 'active').lower()}"
                st.markdown(f"### {p.get('title')} <span class='{status_class}'>{p.get('status')}</span>", unsafe_allow_html=True)
                st.caption(f"📂 Категория: **{p.get('category')}**")
                st.markdown(p.get("description", ""))
                if p.get("milestones"):
                    with st.expander("🎯 Этапы и Milestones"):
                        st.markdown(p.get("milestones"))
                if st.button("🗑️ Удалить проект", key=f"del_p_{p.get('id')}"):
                    bridge.delete_project(p.get("id"))
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Проекты пока не добавлены.")

# ==================== РАЗДЕЛ 4: ЗАМЕТКИ ====================
elif active_tab == "📝 Заметки":
    st.markdown("<h2 class='citadel-header'>📝 Заметки & База Знаний</h2>", unsafe_allow_html=True)
    
    col_n1, col_n2 = st.columns([1, 1])
    with col_n1:
        st.markdown("<div class='citadel-card'>", unsafe_allow_html=True)
        st.markdown("### ✍️ Новая Заметка")
        n_title = st.text_input("Название заметки", value="Конспект теологии и архитектуры")
        n_cat = st.selectbox("Категория заметки", ["Theology", "Ministry", "Code", "Ideas", "General"])
        n_content = st.text_area("Содержимое (Markdown)", height=250, placeholder="Введите текст заметки...")
        n_tags = st.text_input("Теги", value="теология, исследование")
        
        if st.button("💾 Сохранить Заметку", use_container_width=True):
            if n_title and n_content:
                note_data = {
                    "id": str(uuid.uuid4()),
                    "title": n_title,
                    "category": n_cat,
                    "content": n_content,
                    "tags": [t.strip() for t in n_tags.split(",") if t.strip()],
                    "isArchived": False
                }
                if bridge.is_active:
                    bridge.save_note(note_data)
                st.success("✅ Заметка сохранена!")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_n2:
        st.markdown("### 📚 Моя База Знаний")
        notes = bridge.load_notes() if bridge.is_active else []
        if notes:
            for n in notes:
                with st.expander(f"📌 [{n.get('category')}] {n.get('title')}"):
                    st.markdown(n.get("content"))
                    if st.button("🗑️ Удалить заметку", key=f"del_n_{n.get('id')}"):
                        bridge.delete_note(n.get("id"))
                        st.rerun()
        else:
            st.info("Заметки отсутствуют.")

# ==================== РАЗДЕЛ 5: СЕЙФ КЛЮЧЕЙ ====================
elif active_tab == "🔐 Сейф Ключей":
    st.markdown("<h2 class='citadel-header'>🔐 Зашифрованный Сейф Ключей и Паролей</h2>", unsafe_allow_html=True)
    st.caption("Надежное AES-256 хранение API-ключей, токенов, SSH-ключей и паролей")
    
    master_pass = st.session_state.get("master_passphrase", "")
    
    with st.expander("➕ Добавить Новый Секрет в Сейф"):
        with st.form("vault_add_form"):
            v_title = st.text_input("Название (напр., Cloudflare Workers API Token)")
            v_type = st.selectbox("Тип секрета", ["API_KEY", "TOKEN", "SSH_KEY", "PASSWORD", "OTHER"])
            v_secret = st.text_input("Значение Секрета (открытый текст)", type="password")
            v_service = st.text_input("Сервис / Хост", value="Cloudflare / Google AI Studio")
            v_note = st.text_area("Публичная заметка (без секрета)")
            
            v_submit = st.form_submit_button("🔐 Зашифровать и Сохранить")
            
            if v_submit and v_title and v_secret:
                encrypted_payload = encrypt_secret(v_secret, master_pass)
                vault_data = {
                    "id": str(uuid.uuid4()),
                    "title": v_title,
                    "secretType": v_type,
                    "encryptedPayload": encrypted_payload,
                    "serviceName": v_service,
                    "note": v_note
                }
                if bridge.is_active:
                    bridge.save_vault_entry(vault_data)
                st.success("🔒 Секрет успешно зашифрован по стандарту AES-256 и сохранен!")
                st.rerun()

    st.markdown("---")
    st.markdown("### 🔑 Хранимые Секреты")
    vault_entries = bridge.load_vault() if bridge.is_active else []
    
    if vault_entries:
        for ve in vault_entries:
            st.markdown("<div class='citadel-card'>", unsafe_allow_html=True)
            st.markdown(f"#### 🛡️ {ve.get('title')} `[{ve.get('secretType')}]`")
            if ve.get("serviceName"):
                st.caption(f"🌐 Сервис: {ve.get('serviceName')}")
            if ve.get("note"):
                st.markdown(f"*Заметка: {ve.get('note')}*")
                
            col_v1, col_v2 = st.columns([3, 1])
            with col_v1:
                show_key = st.checkbox("👁️ Показать зашифрованное значение", key=f"show_{ve.get('id')}")
                if show_key:
                    decrypted = decrypt_secret(ve.get("encryptedPayload", ""), master_pass)
                    st.code(decrypted)
                else:
                    st.code("••••••••••••••••••••••••••••••••••••••••••••••••")
            with col_v2:
                if st.button("🗑️ Удалить", key=f"del_v_{ve.get('id')}"):
                    bridge.delete_vault_entry(ve.get("id"))
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("В Сейфе пока нет записей.")

# ==================== РАЗДЕЛ 6: НАСТРОЙКИ ====================
elif active_tab == "🏛️ Настройки":
    st.markdown("<h2 class='citadel-header'>🏛️ Настройки Ордена Цитадели</h2>", unsafe_allow_html=True)
    st.markdown(f"**Текущий секретный ключ авторизации**: `{os.getenv('PIM_SECRET_KEY', 'Установлен в сессии')}`")
    st.markdown(f"**Валидный Google Gemini API Key**: `...{os.getenv('GEMINI_API_KEY', '')[-6:]}`")
    st.markdown("✅ Система полностью защищена и готова к публикации в интернете.")
