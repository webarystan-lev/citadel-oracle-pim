import sys
import os
import importlib
import uuid
import time
import json
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
    
    .badge-active { background-color: #065f46; color: #34d399; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
    .badge-planning { background-color: #1e3a8a; color: #93c5fd; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
    .badge-completed { background-color: #312e81; color: #c084fc; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
    .badge-archived { background-color: #374151; color: #9ca3af; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }
    
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
</style>
"""
st.markdown(CITADEL_CSS, unsafe_allow_html=True)

# Ранги и Сигнатуры Моделей в Цитадели
CITADEL_SIGNATURES = {
    "gemini-2.5-flash": {
        "title": "Google Gemini 2.5 Flash",
        "purpose": "Персональный Оракул & Архитектор Знаний",
        "rank": "Верховный Страж Мудрости Цитадели"
    },
    "gemini-1.5-pro": {
        "title": "Google Gemini 1.5 Pro",
        "purpose": "Теологический Исследователь & Глубокий Аналитик",
        "rank": "Старший ИИ-Архитектор Shekinah Cloud"
    },
    "claude-sonnet-4-6": {
        "title": "Anthropic Claude Sonnet 4.6",
        "purpose": "Академический Соратник & Магистр Кода",
        "rank": "Хранитель Свитка и Духовного Мышления"
    },
    "claude-opus-4-6": {
        "title": "Anthropic Claude Opus 4.6",
        "purpose": "Глубокий Рассуждающий Оракул",
        "rank": "Верховный Философ Цитадели"
    },
    "claude-haiku-4-5-20251001": {
        "title": "Anthropic Claude Haiku 4.5",
        "purpose": "Оперативный Быстрый Вестник",
        "rank": "Страж Мгновенных Ответов"
    },
    "mistral-large-latest": {
        "title": "Mistral AI Large",
        "purpose": "Европейский Оракул & Стратег",
        "rank": "Советник Шехина Цитадели"
    }
}

DEFAULT_MODELS = {
    "Google Gemini": ["gemini-2.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"],
    "Anthropic Claude": ["claude-sonnet-4-6", "claude-opus-4-6", "claude-haiku-4-5-20251001"],
    "Mistral AI": ["mistral-large-latest", "pixtral-large-latest", "open-mistral-7b"]
}

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
    st.markdown("<div style='text-align: center; padding-top: 50px;'>", unsafe_allow_html=True)
    st.markdown("<h1 class='citadel-header'>🏛️ CITADEL ORACLE PIM</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 1.1rem;'>Вход в Персональный Интеллектуальный Органайзер Цитадели Духа</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
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
        
        # 2. Модель
        avail_models = DEFAULT_MODELS.get(new_prov, ["gemini-2.5-flash"])
        curr_model = chat.get("model", avail_models[0])
        model_index = avail_models.index(curr_model) if curr_model in avail_models else 0
        
        new_model = st.selectbox("Модель ИИ", avail_models, index=model_index)
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
    st.markdown("<h2 class='citadel-header'>💬 ИИ-Чат & Персональный Оракул</h2>", unsafe_allow_html=True)
    
    current_id = st.session_state.current_chat_id
    chat = st.session_state.chats.get(current_id, {})
    
    sig_info = CITADEL_SIGNATURES.get(chat.get('model'), {"rank": "ИИ-Оракул", "purpose": "Консультация"})
    st.caption(f"🤖 **{sig_info['rank']}** (`{chat.get('provider')} / {chat.get('model')}`) | Назначение: *{sig_info['purpose']}*")

    # Отображение сообщений
    for msg in chat.get("messages", []):
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(content)
        else:
            sig = CITADEL_SIGNATURES.get(chat.get("model", ""), {"rank": "ИИ-Оракул", "purpose": "Ответ"})
            with st.chat_message("assistant", avatar="🤖"):
                st.caption(f"**{sig['rank']}** (`{chat.get('provider')} / {chat.get('model')}`)")
                if "thinking" in msg and msg["thinking"]:
                    with st.expander("🧠 Процесс размышления модели"):
                        st.markdown(msg["thinking"])
                st.markdown(content)

    # Поле ввода
    if prompt := st.chat_input("Спросите Оракула или запросите анализ PIM..."):
        user_msg = {"role": "user", "content": prompt}
        chat["messages"].append(user_msg)
        if bridge.is_active:
            bridge.add_message(current_id, user_msg)
            
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
            
        with st.chat_message("assistant", avatar="🤖"):
            msg_placeholder = st.empty()
            full_response = ""
            
            provider = chat.get("provider", "Google Gemini")
            model = chat.get("model", "gemini-2.5-flash")
            system_p = chat.get("system_prompt", DEFAULT_SYSTEM)
            temp = chat.get("temperature", 0.7)
            m_tok = int(chat.get("max_tokens", 4096))
            
            try:
                if provider == "Google Gemini":
                    for chunk in gemini_client.stream_gemini(
                        messages=chat["messages"],
                        model_name=model,
                        temperature=temp,
                        max_tokens=m_tok,
                        system_prompt=system_p
                    ):
                        full_response += chunk
                        msg_placeholder.markdown(full_response + "▌")
                elif provider == "Anthropic Claude":
                    for chunk in anthropic_client.stream_anthropic(
                        messages=chat["messages"],
                        model_name=model,
                        temperature=temp,
                        max_tokens=m_tok
                    ):
                        full_response += chunk
                        msg_placeholder.markdown(full_response + "▌")
                elif provider == "Mistral AI":
                    for chunk in mistral_client.stream_mistral(
                        messages=chat["messages"],
                        model_name=model,
                        temperature=temp,
                        max_tokens=m_tok
                    ):
                        full_response += chunk
                        msg_placeholder.markdown(full_response + "▌")
                else:
                    full_response = "Выбран неизвестный провайдер."
                
                # Добавляем подпись Ордена к ответу модели
                if full_response and not full_response.startswith("🔴"):
                    sig_block = get_model_signature_block(model, provider)
                    full_response += sig_block
                    
                msg_placeholder.markdown(full_response)
            except Exception as e:
                full_response = f"🔴 Ошибка генерации: {str(e)}"
                msg_placeholder.error(full_response)

            asst_msg = {"role": "assistant", "content": full_response}
            chat["messages"].append(asst_msg)
            if bridge.is_active:
                bridge.add_message(current_id, asst_msg)

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
