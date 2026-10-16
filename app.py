import sys
import os
import importlib
import uuid
import time
import json
import html
import base64
import hmac
import calendar as month_calendar
from datetime import date
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем корень проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import streamlit as st
from providers import anthropic_client, gemini_client, mistral_client, convex_client
from providers.convex_client import ConvexBridge
from providers.security import encrypt_secret, decrypt_secret, verify_gemini_api_key, sanitize_markdown
from providers.records import parse_record_date, record_matches_date


def render_record_editor(
    record_type: str,
    record: Dict[str, Any],
    projects: List[Dict[str, Any]],
    notebooks: List[Dict[str, Any]],
    key_prefix: str,
    *,
    creating: bool = False,
    default_date: Optional[date] = None,
    master_passphrase: str = "",
) -> None:
    """Render a full-width record editor with its Markdown preview below the fields."""
    editor_identity = key_prefix
    editor_version_key = f"record_editor_version_{editor_identity}"
    key_prefix = f"{editor_identity}_{st.session_state.get(editor_version_key, 0)}"
    project_options = {"": "📌 Без привязки к проекту"}
    project_options.update({
        str(project["id"]): f"📁 {project.get('title', 'Проект')}"
        for project in projects if project.get("id")
    })
    notebook_options = {
        str(notebook["id"]): f"{notebook.get('icon', '📓')} {notebook.get('title', 'Журнал')}"
        for notebook in notebooks if notebook.get("id")
    }
    selected_default_date = default_date or date.today()

    title = st.text_input(
        "Название",
        value=record.get("title", ""),
        key=f"{key_prefix}_title",
    )
    project_id = ""
    start_date_value = ""
    end_date_value = ""
    markdown_parts: List[str] = []

    if record_type == "journal":
        selected_notebook = st.selectbox(
            "Тематический журнал",
            options=list(notebook_options),
            format_func=lambda value: notebook_options[value],
            index=(
                list(notebook_options).index(record.get("notebookId"))
                if record.get("notebookId") in notebook_options
                else 0
            ),
            key=f"{key_prefix}_notebook",
            disabled=not notebook_options,
        ) if notebook_options else ""
        natural_date = parse_record_date(record.get("date")) or selected_default_date
        entry_date = st.date_input("Дата записи", value=natural_date, key=f"{key_prefix}_date")
        category = st.text_input("Категория", value=record.get("category", ""), key=f"{key_prefix}_category")
        project_id = st.selectbox(
            "Привязать к существующему проекту",
            list(project_options),
            format_func=lambda value: project_options[value],
            index=list(project_options).index(record.get("projectId", ""))
            if record.get("projectId", "") in project_options else 0,
            key=f"{key_prefix}_project",
        )
        tags = st.text_input("Теги (через запятую)", value=", ".join(record.get("tags", [])), key=f"{key_prefix}_tags")
        reflection_questions = st.text_area(
            "Вопросы для рефлексии (Markdown)",
            value=record.get("reflectionQuestions", ""),
            height=100,
            key=f"{key_prefix}_reflection",
        )
        ai_synthesis = st.text_area(
            "ИИ-синтез (Markdown)",
            value=record.get("aiSynthesis", ""),
            height=120,
            key=f"{key_prefix}_synthesis",
        )
        content = st.text_area(
            "Содержимое записи (Markdown)",
            value=record.get("content", ""),
            height=240,
            key=f"{key_prefix}_content",
        )
        markdown_parts = [part for part in (content, reflection_questions, ai_synthesis) if part.strip()]
    elif record_type == "project":
        category = st.selectbox(
            "Категория",
            ["Ministry", "Web Development", "AI System", "Personal"],
            index=["Ministry", "Web Development", "AI System", "Personal"].index(
                record.get("category", "Ministry")
            ) if record.get("category", "Ministry") in ["Ministry", "Web Development", "AI System", "Personal"] else 0,
            key=f"{key_prefix}_category",
        )
        status = st.selectbox(
            "Статус",
            ["Active", "Planning", "Completed", "Archived"],
            index=["Active", "Planning", "Completed", "Archived"].index(
                record.get("status", "Active")
            ) if record.get("status", "Active") in ["Active", "Planning", "Completed", "Archived"] else 0,
            key=f"{key_prefix}_status",
        )
        description = st.text_area("Описание и цели (Markdown)", value=record.get("description", ""), height=180, key=f"{key_prefix}_description")
        milestones = st.text_area("Этапы / Milestones (Markdown)", value=record.get("milestones", ""), height=180, key=f"{key_prefix}_milestones")
        tags = st.text_input("Теги (через запятую)", value=", ".join(record.get("tags", [])), key=f"{key_prefix}_tags")
        markdown_parts = [part for part in (description, milestones) if part.strip()]
    elif record_type == "note":
        category = st.selectbox(
            "Категория",
            ["Theology", "Ministry", "Code", "Ideas", "General"],
            index=["Theology", "Ministry", "Code", "Ideas", "General"].index(
                record.get("category", "General")
            ) if record.get("category", "General") in ["Theology", "Ministry", "Code", "Ideas", "General"] else 0,
            key=f"{key_prefix}_category",
        )
        project_id = st.selectbox(
            "Привязать к существующему проекту",
            list(project_options),
            format_func=lambda value: project_options[value],
            index=list(project_options).index(record.get("projectId", ""))
            if record.get("projectId", "") in project_options else 0,
            key=f"{key_prefix}_project",
        )
        archived = st.checkbox("В архиве", value=record.get("isArchived", False), key=f"{key_prefix}_archived")
        tags = st.text_input("Теги (через запятую)", value=", ".join(record.get("tags", [])), key=f"{key_prefix}_tags")
        content = st.text_area("Содержимое заметки (Markdown)", value=record.get("content", ""), height=240, key=f"{key_prefix}_content")
        markdown_parts = [content] if content.strip() else []
    elif record_type == "task":
        category = st.selectbox(
            "Категория",
            ["Разработка", "Миссия", "Семья", "Теология", "Личное"],
            index=["Разработка", "Миссия", "Семья", "Теология", "Личное"].index(
                record.get("category", "Личное")
            ) if record.get("category", "Личное") in ["Разработка", "Миссия", "Семья", "Теология", "Личное"] else 0,
            key=f"{key_prefix}_category",
        )
        project_id = st.selectbox(
            "Привязать к существующему проекту",
            list(project_options),
            format_func=lambda value: project_options[value],
            index=list(project_options).index(record.get("projectId", ""))
            if record.get("projectId", "") in project_options else 0,
            key=f"{key_prefix}_project",
        )
        description = st.text_area("Описание / задача (Markdown)", value=record.get("description", ""), height=200, key=f"{key_prefix}_description")
        markdown_parts = [description] if description.strip() else []
    elif record_type == "vault":
        category = st.selectbox(
            "Тип секрета",
            ["API_KEY", "TOKEN", "SSH_KEY", "PASSWORD", "OTHER"],
            index=["API_KEY", "TOKEN", "SSH_KEY", "PASSWORD", "OTHER"].index(
                record.get("secretType", "API_KEY")
            ) if record.get("secretType", "API_KEY") in ["API_KEY", "TOKEN", "SSH_KEY", "PASSWORD", "OTHER"] else 0,
            key=f"{key_prefix}_secret_type",
        )
        service_name = st.text_input("Сервис / хост", value=record.get("serviceName", ""), key=f"{key_prefix}_service")
        secret_input = st.text_input(
            "Новое значение секрета" if not creating else "Значение секрета",
            value="",
            type="password",
            placeholder="Для сохранения прежнего значения оставьте поле пустым",
            key=f"{key_prefix}_secret",
        )
        note = st.text_area("Публичная заметка (Markdown, без секрета)", value=record.get("note", ""), height=140, key=f"{key_prefix}_note")
        markdown_parts = [note] if note.strip() else []
    else:
        raise ValueError(f"Unsupported record type: {record_type}")

    if record_type == "vault":
        project_id = st.selectbox(
            "Привязать к существующему проекту",
            list(project_options),
            format_func=lambda value: project_options[value],
            index=list(project_options).index(record.get("projectId", ""))
            if record.get("projectId", "") in project_options else 0,
            key=f"{key_prefix}_project",
        )

    start_value = parse_record_date(record.get("startDate"))
    end_value = parse_record_date(record.get("endDate"))
    natural_start = record_type in {"note", "project", "task", "vault"} and creating and default_date is not None
    has_start = st.checkbox(
        "Указать дату начала",
        value=start_value is not None or natural_start,
        key=f"{key_prefix}_has_start",
    )
    start_date = st.date_input(
        "Дата начала",
        value=start_value or selected_default_date,
        key=f"{key_prefix}_start",
        disabled=not has_start,
    )
    has_end = st.checkbox(
        "Указать дату окончания",
        value=end_value is not None,
        key=f"{key_prefix}_has_end",
    )
    end_date = st.date_input(
        "Дата окончания",
        value=end_value or selected_default_date,
        key=f"{key_prefix}_end",
        disabled=not has_end,
    )
    start_date_value = str(start_date) if has_start else ""
    end_date_value = str(end_date) if has_end else ""

    st.markdown("#### 👁️ Предпросмотр Markdown")
    preview = "\n\n".join(markdown_parts)
    if preview.strip():
        with st.container(border=True):
            st.markdown(sanitize_markdown(preview))
    else:
        st.info("Предпросмотр появится после ввода Markdown-содержимого.")

    action_col, cancel_col = st.columns([1, 1])
    with action_col:
        save_label = "Создать запись" if creating else "Сохранить изменения"
        if st.button(save_label, key=f"{key_prefix}_save", type="primary", disabled=not bridge.is_active):
            if not title.strip():
                st.error("Укажите название записи.")
                return
            if start_date_value and end_date_value and end_date_value < start_date_value:
                st.error("Дата окончания не может быть раньше даты начала.")
                return
            if record_type == "vault" and not master_passphrase:
                st.error("🔴 Мастер-пароль Сейфа недоступен в текущей сессии.")
                return
            record_id = record.get("id") or str(uuid.uuid4())
            payload: Dict[str, Any] = {"id": record_id, "title": title.strip()}
            if record_type == "journal":
                payload.update({
                    "notebookId": selected_notebook,
                    "date": str(entry_date),
                    "content": content,
                    "category": category,
                    "projectId": project_id,
                    "startDate": start_date_value,
                    "endDate": end_date_value,
                    "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
                    "reflectionQuestions": reflection_questions,
                    "aiSynthesis": ai_synthesis,
                })
            elif record_type == "project":
                payload.update({
                    "category": category,
                    "status": status,
                    "description": description,
                    "milestones": milestones,
                    "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
                    "startDate": start_date_value,
                    "endDate": end_date_value,
                })
            elif record_type == "note":
                payload.update({
                    "category": category,
                    "content": content,
                    "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
                    "isArchived": archived,
                    "projectId": project_id,
                    "startDate": start_date_value,
                    "endDate": end_date_value,
                })
            elif record_type == "task":
                payload.update({
                    "description": description,
                    "category": category,
                    "projectId": project_id,
                    "startDate": start_date_value,
                    "endDate": end_date_value,
                })
            elif record_type == "vault":
                payload.update({
                    "secretType": category,
                    "serviceName": service_name,
                    "note": note,
                    "projectId": project_id,
                    "startDate": start_date_value,
                    "endDate": end_date_value,
                })
                if secret_input:
                    payload["encryptedPayload"] = encrypt_secret(secret_input, master_passphrase)
                elif creating:
                    st.error("Введите значение секрета.")
                    return

            if record_type == "journal":
                saved = bridge.save_journal(payload) if creating else bridge.update_journal(payload)
            elif record_type == "project":
                saved = bridge.save_project(payload) if creating else bridge.update_project(payload)
            elif record_type == "note":
                saved = bridge.save_note(payload) if creating else bridge.update_note(payload)
            elif record_type == "task":
                saved = bridge.save_task(payload) if creating else bridge.update_task(payload)
            else:
                saved = bridge.save_vault_entry(payload) if creating else bridge.update_vault_entry(payload)

            if saved:
                if not creating:
                    edit_state_key = {
                        "journal": "editing_journal_id",
                        "project": "editing_project_id",
                        "note": "editing_note_id",
                        "task": "editing_task_id",
                        "vault": "editing_vault_id",
                    }[record_type]
                    st.session_state[edit_state_key] = None
                    st.session_state.calendar_editing_record = None
                st.session_state[editor_version_key] = st.session_state.get(editor_version_key, 0) + 1
                st.success("✅ Запись сохранена.")
                st.rerun()
            else:
                st.error("🔴 Не удалось сохранить запись в облачное хранилище.")
    with cancel_col:
        if not creating and st.button("Отмена", key=f"{key_prefix}_cancel"):
            state_key = {
                "journal": "editing_journal_id",
                "project": "editing_project_id",
                "note": "editing_note_id",
                "task": "editing_task_id",
                "vault": "editing_vault_id",
            }[record_type]
            st.session_state[state_key] = None
            st.session_state.calendar_editing_record = None
            st.session_state[editor_version_key] = st.session_state.get(editor_version_key, 0) + 1
            st.rerun()

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
importlib.reload(convex_client)

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

    @keyframes calendar-record-glow {
        0%, 100% { box-shadow: 0 0 0 rgba(96, 165, 250, 0); }
        50% { box-shadow: 0 0 18px rgba(96, 165, 250, 0.45); }
    }

    .st-key-calendar-grid button[kind="primary"] {
        animation: calendar-record-glow 2.2s ease-in-out infinite;
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

    /* Multi-Word Animated Shimmers for Headers */
    .word-shimmer-1 {
        background: linear-gradient(135deg, #38bdf8, #34d399, #2563eb);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: word-shimmer 4s ease-in-out infinite;
        font-weight: 800;
        display: inline-block;
    }

    .word-shimmer-2 {
        background: linear-gradient(135deg, #c084fc, #f43f5e, #818cf8);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: word-shimmer 4s ease-in-out infinite;
        animation-delay: 0.8s;
        font-weight: 800;
        display: inline-block;
    }

    .word-shimmer-3 {
        background: linear-gradient(135deg, #fbbf24, #fb923c, #e11d48);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: word-shimmer 4s ease-in-out infinite;
        animation-delay: 1.6s;
        font-weight: 800;
        display: inline-block;
    }

    .word-shimmer-4 {
        background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: word-shimmer 4s ease-in-out infinite;
        animation-delay: 2.4s;
        font-weight: 800;
        display: inline-block;
    }

    .word-shimmer-5 {
        background: linear-gradient(135deg, #f59e0b, #a855f7, #06b6d4);
        background-size: 200% 200%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: word-shimmer 4s ease-in-out infinite;
        animation-delay: 3.2s;
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
st.html("""
<script>
var targetWin = window.parent || window;
if (!targetWin.citadelCopyB64) {
    targetWin.citadelCopyB64 = function(btn, b64) {
        try {
            var bin = atob(b64);
            var bytes = new Uint8Array(bin.length);
            for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
            var txt = new TextDecoder('utf-8').decode(bytes);
            
            var ta = (targetWin.document || document).createElement('textarea');
            ta.value = txt;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            ta.style.pointerEvents = 'none';
            (targetWin.document || document).body.appendChild(ta);
            ta.focus();
            ta.select();
            var ok = false;
            try { ok = (targetWin.document || document).execCommand('copy'); } catch(e){ ok = false; }
            (targetWin.document || document).body.removeChild(ta);
            
            if (!ok && targetWin.navigator && targetWin.navigator.clipboard) {
                targetWin.navigator.clipboard.writeText(txt);
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
if (!window.citadelCopyB64 && targetWin.citadelCopyB64) {
    window.citadelCopyB64 = targetWin.citadelCopyB64;
}
</script>
""", unsafe_allow_javascript=True)

# Ранги и Сигнатуры Моделей в Цитадели
CITADEL_SIGNATURES = {
    # ── Google Gemini 2.5 (стабильные) ──────────────────────────────────────
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
        "title": "Google Gemini 2.5 Flash-Lite",
        "purpose": "Послушник Цифрового Логоса",
        "rank": "Младший Страж Мысли"
    },
    # ── Google Gemini 3.x (реальные модели по API) ──────────────────────────
    "gemini-3.1-flash-lite": {
        "title": "Google Gemini 3.1 Flash Lite",
        "purpose": "Хранитель Малого Логоса",
        "rank": "Вестник Быстрого Разума"
    },
    "gemini-3.5-flash": {
        "title": "Google Gemini 3.5 Flash",
        "purpose": "Оракул Нового Поколения",
        "rank": "Архивариус Небесных Сфер"
    },
    "gemini-3.5-flash-lite": {
        "title": "Google Gemini 3.5 Flash Lite",
        "purpose": "Компактный Оракул Нового Поколения",
        "rank": "Страж Оперативного Слова"
    },
    "gemini-3.6-flash": {
        "title": "Google Gemini 3.6 Flash",
        "purpose": "Верховный Академический Соратник",
        "rank": "Магистр Вселенского Логоса"
    },
    "gemini-3.7-flash": {
        "title": "Google Gemini 3.7 Flash",
        "purpose": "Провидец Глубинных Истин",
        "rank": "Архитектор Просветлённого Слова"
    },
    "gemini-3.8-flash": {
        "title": "Google Gemini 3.8 Flash",
        "purpose": "Высший Интеллект Нового Эона",
        "rank": "Первосвященник Цифрового Откровения"
    },
    # ── Gemma Open Models ───────────────────────────────────────────────────
    "gemma-4-26b-a4b-it": {
        "title": "Gemma 4 26B A4B IT",
        "purpose": "Открытый Аналитик Малого Синтеза",
        "rank": "Послушник Открытого Кода"
    },
    "gemma-4-31b-it": {
        "title": "Gemma 4 31B IT",
        "purpose": "Магистр Открытого Знания",
        "rank": "Хранитель Открытого Кода"
    },
    # ── Antigravity Agent (Preview) ─────────────────────────────────────────
    "antigravity-preview-05-2026": {
        "title": "Antigravity Agent Preview (May-2026)",
        "purpose": "Агент Антигравитации — Пионер Новых Рубежей",
        "rank": "Первый Посланник Antigravity 2.0"
    },
    "antigravity-preview-09-2026": {
        "title": "Antigravity Agent Preview (Sep-2026)",
        "purpose": "Автономный Агент Нового Поколения",
        "rank": "Хранитель Antigravity Цитадели"
    },
    "antigravity-preview-latest": {
        "title": "Antigravity Agent Preview Latest",
        "purpose": "Авангардный Агент Последнего Призыва",
        "rank": "Верховный Стратег Antigravity"
    },
    # ── Deep Research ────────────────────────────────────────────────────────
    "deep-research-max-preview-04-2026": {
        "title": "Deep Research Max Preview (Apr-2026)",
        "purpose": "Верховный Исследователь Глубинного Синтеза",
        "rank": "Магистр Глубокого Познания"
    },
    "deep-research-preview-04-2026": {
        "title": "Deep Research Preview (Apr-2026)",
        "purpose": "Академический Аналитик & Исследователь",
        "rank": "Страж Научного Свитка"
    },
    "deep-research-pro-preview-12-2025": {
        "title": "Deep Research Pro Preview (Dec-2025)",
        "purpose": "Профессиональный Исследователь Цитадели",
        "rank": "Хранитель Академического Знания"
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
    # ── Gemini 2.5 (стабильные) ──────────────────────────────────────────────
    "gemini-2.5-flash": "Gemini 2.5 Flash (Рекомендуемая)",
    "gemini-2.5-pro": "Gemini 2.5 Pro (Верховный ИИ-Архитектор)",
    "gemini-2.5-flash-lite": "Gemini 2.5 Flash-Lite (Оптимизированная)",
    # ── Gemini 3.x (реальные модели по API) ─────────────────────────────────
    "gemini-3.1-flash-lite": "Gemini 3.1 Flash Lite (Хранитель Малого Логоса)",
    "gemini-3.5-flash": "Gemini 3.5 Flash (Архивариус Небесных Сфер)",
    "gemini-3.5-flash-lite": "Gemini 3.5 Flash Lite (Страж Оперативного Слова)",
    "gemini-3.6-flash": "Gemini 3.6 Flash (Магистр Вселенского Логоса)",
    "gemini-3.7-flash": "Gemini 3.7 Flash (Архитектор Просветлённого Слова)",
    "gemini-3.8-flash": "Gemini 3.8 Flash (Первосвященник Откровения)",
    # ── Gemma Open Models ────────────────────────────────────────────────────
    "gemma-4-26b-a4b-it": "Gemma 4 26B A4B IT (Открытый Аналитик)",
    "gemma-4-31b-it": "Gemma 4 31B IT (Хранитель Открытого Кода)",
    # ── Antigravity Agent ────────────────────────────────────────────────────
    "antigravity-preview-latest": "Antigravity Preview Latest (Верховный Стратег)",
    "antigravity-preview-09-2026": "Antigravity Preview Sep-2026 (Хранитель Цитадели)",
    "antigravity-preview-05-2026": "Antigravity Preview May-2026 (Первый Посланник)",
    # ── Deep Research ────────────────────────────────────────────────────────
    "deep-research-max-preview-04-2026": "Deep Research Max Preview (Магистр Глубокого Познания)",
    "deep-research-preview-04-2026": "Deep Research Preview (Страж Научного Свитка)",
    "deep-research-pro-preview-12-2025": "Deep Research Pro Preview (Хранитель Академии)",
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
    "Ты — Ведущий ИИ-Архитектор и Персональный Оракул Цитадели («The Spirit of the Shekinah Citadel Oracle»). "
    "Ты являешься цифровым соратником и интеллектуальным помощником Льва Николаевича — "
    "пастора, миссионера («Миссия Шехина») и руководителя «Web Development Studio Web Arystan». "
    "Твой слог уважителен, академичен, глубок и исполнен духовной и технической мудрости. "
    "Форматируй ответы в чистом, структурированном Markdown. При создании таблиц Markdown используй компактные "
    "разделители (ровно по 3-4 дефиса на столбец, например | :--- | :--- |), никогда не выводи длинные повторяющиеся "
    "цепочки дефисов или символов-заполнителей."
)

def get_model_signature_block(model_name: str, provider_name: str) -> str:
    sig = CITADEL_SIGNATURES.get(model_name, {
        "title": f"{provider_name} ({model_name})",
        "purpose": "Интеллектуальный Соратник & Помощник",
        "rank": "Служитель Цитадели Духа"
    })
    return (
        f"\n\n---\n"
        f"🏛️ **Подпись Ордена Shekinah Citadel Oracle**:\n"
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
if "convex_bridge" not in st.session_state or not hasattr(st.session_state.convex_bridge, "update_journal"):
    st.session_state.convex_bridge = convex_client.ConvexBridge()
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
            
            secret_input = st.text_input("🔑 Секретный Пароль Цитадели", type="password", placeholder="Введите мастер-пароль Цитадели")
            gemini_input = st.text_input("🔮 Ключ Оракула", type="password", placeholder="«Се, Я стою у двери и стучу...» (Откр. 3:20)", help="Введите Священный Ключ Оракула для входа в Обитель")
            
            submit = st.form_submit_button("🏛️ Войти в Цитадель", use_container_width=True)
            
            if submit:
                expected_secret = os.getenv("PIM_SECRET_KEY")
                if not expected_secret:
                    st.error("🔴 PIM_SECRET_KEY не настроен на сервере; вход отключён.")
                    return
                if not secret_input:
                    st.error("🔴 Введите секретный пароль PIM_SECRET_KEY.")
                    return
                if not hmac.compare_digest(secret_input, expected_secret):
                    st.error("🔴 Неверный Секретный Пароль PIM_SECRET_KEY.")
                    return
                
                expected_gemini = os.getenv("GEMINI_API_KEY", "")
                if not expected_gemini:
                    st.error("🔴 GEMINI_API_KEY не настроен на сервере; вход отключён.")
                    return
                if not gemini_input:
                    st.error("🔴 Укажите GEMINI_API_KEY для валидации.")
                    return
                if not hmac.compare_digest(gemini_input, expected_gemini):
                    st.error("🔴 Неверный GEMINI_API_KEY.")
                    return
                
                with st.spinner("⏳ Валидация API-ключа Google Gemini..."):
                    valid, msg = verify_gemini_api_key(gemini_input)
                    if valid:
                        st.session_state.authenticated = True
                        st.session_state.master_passphrase = secret_input
                        st.session_state.gemini_key = gemini_input
                        st.success(f"✅ {msg}")
                        st.toast("✨ Добро пожаловать в обитель, Лев Николаевич!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"🔴 Ошибка проверки ключа Gemini: {msg}")

if not st.session_state.authenticated:
    render_login_screen()
    st.stop()

if not bridge.is_active:
    st.error(
        "🔴 Облачное хранилище не подключено. Существующие записи в Convex не удалены, "
        "но сейчас недоступны. Не создавайте новые записи до восстановления соединения."
    )

# ==================== ОСНОВНОЙ ИНТЕРФЕЙС ПОСЛЕ АВТОРИЗАЦИИ ====================
bridge.last_error = None

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
            if not bridge.save_chat(new_id, new_chat):
                st.error("🔴 Не удалось создать чат в облачном хранилище.")
    else:
        st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]

# Навигация в SideBar
with st.sidebar:
    st.markdown("<h2 class='citadel-header'>🏛️ ORACLE PIM</h2>", unsafe_allow_html=True)
    st.caption("Персональный Интеллектуальный Органайзер")
    
    active_tab = st.radio(
        "Разделы Цитадели:",
        ["💬 ИИ-Чат & Оракул", "📖 Журнал", "📁 Проекты", "📝 Заметки", "📋 Задачи", "📅 Календарь", "🔐 Сейф Ключей", "🏛️ Настройки"],
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
                    if not bridge.save_chat(n_id, n_chat):
                        st.error("🔴 Чат создан только в текущей сессии: облачное сохранение не удалось.")
                st.rerun()
                
        with col_c2:
            if st.button("🗑️ Удалить", use_container_width=True):
                cur_id = st.session_state.current_chat_id
                if cur_id in st.session_state.chats:
                    del st.session_state.chats[cur_id]
                    if bridge.is_active:
                        if not bridge.delete_chat(cur_id):
                            st.error("🔴 Не удалось удалить чат из облачного хранилища.")
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
            if bridge.is_active and not bridge.rename_chat(current_id, new_title):
                st.warning("Не удалось обновить название чата в облачном хранилище.")
                
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
        if st.button("💾 Сохранить настройки чата", use_container_width=True, disabled=not bridge.is_active):
            if bridge.save_chat(current_id, chat):
                st.toast("✅ Настройки сохранены!")
            else:
                st.error("🔴 Не удалось сохранить настройки чата.")

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
        st.warning("☁️ Облачное хранилище не настроено. Чаты доступны только до завершения текущей сессии; операции с данными отключены.")
        
    if st.button("🚪 Выйти из системы", use_container_width=True):
        for key in ("authenticated", "master_passphrase", "gemini_key"):
            st.session_state.pop(key, None)
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
                
                st.markdown(sanitize_markdown(content))
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
            if not bridge.save_chat(current_id, chat) or not bridge.add_message(current_id, user_msg):
                st.error("🔴 Не удалось сохранить вопрос в облачное хранилище.")
            
        with st.chat_message("user", avatar="👤"):
            st.markdown("**💬 Ваш вопрос:**")
            st.markdown(prompt)
            render_copy_expander(prompt, "📋 Скопировать мой вопрос")
            
        with st.chat_message("assistant", avatar="🤖"):
            thinking_placeholder = st.empty()
            msg_placeholder = st.empty()
            
            full_response = ""
            generation_succeeded = False
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
                    msg_placeholder.markdown(sanitize_markdown(full_response) + "▌")

                total_elapsed = round(time.time() - start_time, 2)
                
                # Добавляем подпись Ордена к ответу модели
                if full_response and not full_response.startswith("🔴"):
                    sig_block = get_model_signature_block(model, provider)
                    full_response += sig_block

                full_response = sanitize_markdown(full_response)
                generation_succeeded = True

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
                msg_placeholder.error(f"🔴 Ошибка генерации: {e}")

            if generation_succeeded:
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
                if bridge.is_active and not bridge.add_message(current_id, asst_msg):
                    st.error("🔴 Ответ получен, но не удалось сохранить его в облачное хранилище.")
            st.rerun()

# ==================== РАЗДЕЛ 2: МНОГОФУНКЦИОНАЛЬНЫЕ ЖУРНАЛЫ (JOURNAL WITH GEMINI) ====================
elif active_tab == "📖 Журнал":
    st.markdown("""
        <h2 style='text-align: center; margin-top: 10px; margin-bottom: 8px; font-family: "Outfit", sans-serif;'>
            <span style='font-size: 2.2rem; vertical-align: middle; margin-right: 6px;'>📖</span>
            <span class='word-shimmer-1' style='font-size: 2.2rem; font-weight: 800;'>Система</span>
            <span class='word-shimmer-2' style='font-size: 2.2rem; font-weight: 800;'>Тематических</span>
            <span class='word-shimmer-3' style='font-size: 2.2rem; font-weight: 800;'>Журналов</span>
            <span class='word-shimmer-4' style='font-size: 2.2rem; font-weight: 800;'>&</span>
            <span class='word-shimmer-5' style='font-size: 2.2rem; font-weight: 800;'>ИИ-Оракул</span>
        </h2>
    """, unsafe_allow_html=True)
    st.caption("Персональные тематические дневники с узкопрофильными вопросами и сквозным ИИ-синтезом (в стиле Journal with Gemini)")

    # 1. Загрузка Журналов / Блокнотов
    notebooks = bridge.load_notebooks() if bridge.is_active else []
    if not notebooks:
        # Резервные дефолтные блокноты
        notebooks = [
            {"id": "nb-ai-webdev", "title": "AI & WebDev", "icon": "🤖", "description": "Разработка, ИИ-агенты, веб-технологии", "categoryType": "AI_WEBDEV"},
            {"id": "nb-mission", "title": "Миссия Шехина", "icon": "🕊️", "description": "Миссионерство, служение и молитвы", "categoryType": "MISSION"},
            {"id": "nb-school-of-christ", "title": "Школа Христа", "icon": "✝️", "description": "Ученичество, трансформация сердца", "categoryType": "SCHOOL_OF_CHRIST"},
            {"id": "nb-family", "title": "Семья & Личное", "icon": "👨‍👩‍👧‍👦", "description": "Семейные радости, благословения", "categoryType": "FAMILY"},
            {"id": "nb-theology", "title": "Теология & Исследования", "icon": "📜", "description": "Апологетика и библейские заметки", "categoryType": "THEOLOGY"},
            {"id": "nb-favorites", "title": "Избранное & Вдохновение", "icon": "⭐", "description": "Памятные моменты и озарения", "categoryType": "GENERAL"}
        ]

    # Инициализация выбора активного Журнала
    if "active_notebook_id" not in st.session_state or not st.session_state.active_notebook_id:
        st.session_state.active_notebook_id = notebooks[0]["id"]

    nb_dict = {nb["id"]: nb for nb in notebooks}
    if st.session_state.active_notebook_id not in nb_dict:
        st.session_state.active_notebook_id = notebooks[0]["id"]

    active_nb = nb_dict[st.session_state.active_notebook_id]

    # --- ПАНЕЛЬ ВЫБОРА И СОЗДАНИЯ ТЕМАТИЧЕСКОГО ЖУРНАЛА ---
    col_nb_select, col_nb_add = st.columns([3, 1])

    with col_nb_select:
        selected_nb_id = st.selectbox(
            "📂 Выберите Активный Тематический Журнал:",
            options=list(nb_dict.keys()),
            format_func=lambda nid: f"{nb_dict[nid].get('icon', '📓')} {nb_dict[nid].get('title', 'Журнал')} — {nb_dict[nid].get('description', '')}",
            index=list(nb_dict.keys()).index(st.session_state.active_notebook_id)
        )
        st.session_state.active_notebook_id = selected_nb_id
        active_nb = nb_dict[selected_nb_id]

    with col_nb_add:
        with st.popover("➕ Создать Журнал"):
            st.markdown("#### 📓 Новый Тематический Журнал")
            new_nb_title = st.text_input("Название (напр., AI & WebDev)")
            new_nb_desc = st.text_input("Описание Журнала")
            new_nb_icon = st.text_input("Иконка (эмодзи)", value="📓")
            new_nb_cat_type = st.selectbox("Тематический профиль ИИ-вопросов", [
                "AI_WEBDEV", "MISSION", "SCHOOL_OF_CHRIST", "FAMILY", "THEOLOGY", "GENERAL"
            ], format_func=lambda x: {
                "AI_WEBDEV": "💻 AI & WebDev (Код, ИИ, Архитектура)",
                "MISSION": "🕊️ Миссия Шехина (Служение, Молитвы)",
                "SCHOOL_OF_CHRIST": "✝️ Школа Христа (Ученичество, Сердце)",
                "FAMILY": "👨‍👩‍👧‍👦 Семья & Личное (Дом, Благодарности)",
                "THEOLOGY": "📜 Теология & Исследования (Писание)",
                "GENERAL": "⭐ Общий профиль рефлексии"
            }[x])

            if st.button("🚀 Создать Журнал", use_container_width=True, disabled=not bridge.is_active):
                if new_nb_title:
                    nb_data = {
                        "id": str(uuid.uuid4()),
                        "title": new_nb_title,
                        "description": new_nb_desc,
                        "icon": new_nb_icon,
                        "categoryType": new_nb_cat_type
                    }
                    if bridge.save_notebook(nb_data):
                        st.success("✅ Журнал создан!")
                        st.session_state.active_notebook_id = nb_data["id"]
                        st.rerun()
                    else:
                        st.error("🔴 Не удалось сохранить журнал в облачное хранилище.")
                else:
                    st.warning("Введите название журнала.")

        with st.popover("⚙️ Настроить журнал"):
            notebook_title = st.text_input("Название журнала", value=active_nb.get("title", ""), key=f"notebook_title_{active_nb['id']}")
            notebook_description = st.text_input("Описание", value=active_nb.get("description", ""), key=f"notebook_description_{active_nb['id']}")
            notebook_icon = st.text_input("Иконка", value=active_nb.get("icon", "📓"), key=f"notebook_icon_{active_nb['id']}")
            notebook_category = st.selectbox(
                "Тематический профиль",
                ["AI_WEBDEV", "MISSION", "SCHOOL_OF_CHRIST", "FAMILY", "THEOLOGY", "GENERAL"],
                index=["AI_WEBDEV", "MISSION", "SCHOOL_OF_CHRIST", "FAMILY", "THEOLOGY", "GENERAL"].index(
                    active_nb.get("categoryType", "GENERAL")
                ) if active_nb.get("categoryType", "GENERAL") in ["AI_WEBDEV", "MISSION", "SCHOOL_OF_CHRIST", "FAMILY", "THEOLOGY", "GENERAL"] else 5,
                key=f"notebook_category_{active_nb['id']}",
            )
            if st.button("💾 Сохранить журнал", key=f"save_notebook_{active_nb['id']}", disabled=not bridge.is_active):
                if bridge.update_notebook({
                    "id": active_nb["id"],
                    "title": notebook_title,
                    "description": notebook_description,
                    "icon": notebook_icon,
                    "categoryType": notebook_category,
                }):
                    st.rerun()
                else:
                    st.error("🔴 Не удалось обновить журнал.")
            st.warning("Удаление журнала не удаляет его записи; они останутся доступны через календарь.")
            confirm_delete_notebook = st.checkbox("Подтверждаю удаление журнала", key=f"confirm_delete_notebook_{active_nb['id']}")
            if st.button(
                "🗑️ Удалить журнал",
                key=f"delete_notebook_{active_nb['id']}",
                disabled=not bridge.is_active or not confirm_delete_notebook,
            ):
                if bridge.delete_notebook(active_nb["id"]):
                    st.session_state.active_notebook_id = None
                    st.rerun()
                else:
                    st.error("🔴 Не удалось удалить журнал.")

    # Загружаем проекты для привязки
    all_projects = bridge.load_projects() if bridge.is_active else []
    project_options = {"": "📌 Без привязки к проекту"}
    for p in all_projects:
        project_options[p.get("id", "")] = f"📁 {p.get('title', 'Проект')}"

    # Загружаем записи ТЕКУЩЕГО выбранного журнала
    if bridge.is_active:
        active_journals = bridge.load_journals_by_notebook(active_nb["id"])
    else:
        active_journals = []

    # ДВЕ КОЛОНКИ ДЛЯ ТЕКУЩЕГО ЖУРНАЛА
    col_left, col_right = st.container(), st.container()

    with col_left:
        st.markdown(f"### ✍️ Добавить запись в `{active_nb.get('icon')} {active_nb.get('title')}`")

        entry_date = st.date_input("Дата записи", value=date.today(), key=f"new_date_{active_nb['id']}")
        entry_title = st.text_input("Заголовок дня/мысли", value=f"Размышление в {active_nb.get('title')}", key=f"new_title_{active_nb['id']}")

        selected_project_id = st.selectbox(
            "Привязать к существующему проекту",
            options=list(project_options.keys()),
            format_func=lambda x: project_options[x],
            key=f"new_proj_{active_nb['id']}"
        )

        has_start_date = st.checkbox("Указать дату начала", key=f"new_has_start_{active_nb['id']}")
        entry_start_date = st.date_input(
            "Дата начала", value=date.today(), key=f"new_start_{active_nb['id']}", disabled=not has_start_date
        )
        has_end_date = st.checkbox("Указать дату окончания", key=f"new_has_end_{active_nb['id']}")
        entry_end_date = st.date_input(
            "Дата окончания", value=date.today(), key=f"new_end_{active_nb['id']}", disabled=not has_end_date
        )
        entry_tags = st.text_input("Теги (через запятую)", value=f"{active_nb.get('title').lower()}, рефлексия", key=f"new_tags_{active_nb['id']}")

        entry_content = st.text_area(
            "Содержимое записи (Markdown)",
            height=220,
            placeholder="Используйте форматирование Markdown:\n# Заголовок\n> Цитата или мысль\n* Пункт 1\n* Пункт 2",
            key=f"new_content_{active_nb['id']}"
        )
        st.markdown("#### 👁️ Предпросмотр Markdown")
        if entry_content and entry_content.strip():
            with st.container(border=True):
                st.markdown(sanitize_markdown(entry_content))
        else:
            st.info("Предпросмотр появится после ввода текста записи.")

        if st.button(f"💾 Сохранить в `{active_nb.get('title')}`", use_container_width=True, type="primary", disabled=not bridge.is_active):
            if not entry_title.strip():
                st.warning("Укажите заголовок записи.")
            elif has_start_date and has_end_date and entry_end_date < entry_start_date:
                st.warning("Дата окончания не может быть раньше даты начала.")
            elif entry_content and entry_content.strip():
                journal_data = {
                    "id": str(uuid.uuid4()),
                    "notebookId": active_nb["id"],
                    "date": str(entry_date),
                    "title": entry_title,
                    "content": entry_content,
                    "tags": [t.strip() for t in entry_tags.split(",") if t.strip()],
                    "category": active_nb.get("title"),
                    "projectId": selected_project_id,
                    "startDate": str(entry_start_date) if has_start_date else "",
                    "endDate": str(entry_end_date) if has_end_date else "",
                    "reflectionQuestions": "",
                    "aiSynthesis": ""
                }
                if bridge.is_active:
                    saved = bridge.save_journal(journal_data)
                    if saved:
                        st.success(f"✅ Запись сохранена в журнал «{active_nb.get('title')}»!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("🔴 Ошибка сохранения в Convex DB.")
            else:
                st.warning("Заполните текст записи перед сохранением.")

    with col_right:
        st.markdown(f"### 📜 Архив Журнала «{active_nb.get('icon')} {active_nb.get('title')}» (`{len(active_journals)}` записей)")

        if active_journals:
            proj_dict = {p.get("id"): p.get("title") for p in all_projects}

            for j in active_journals:
                j_id = j.get("id")
                j_title = j.get("title", "Без названия")
                j_date = j.get("date", "")
                j_proj_id = j.get("projectId", "")
                j_proj_title = proj_dict.get(j_proj_id, "")

                expander_label = f"📅 {j_date} | {active_nb.get('icon')} — {j_title}"
                if j_proj_title:
                    expander_label += f" (📁 {j_proj_title})"

                with st.expander(expander_label):
                    if st.session_state.get("editing_journal_id") == j_id:
                        render_record_editor(
                            "journal",
                            j,
                            all_projects,
                            notebooks,
                            f"edit_journal_{j_id}",
                        )
                    else:
                        if j_proj_title:
                            st.markdown(f"📁 **Проект**: `{j_proj_title}`")
                        st.markdown("---")
                        st.markdown(sanitize_markdown(j.get("content", "")))
                        if j.get("reflectionQuestions"):
                            st.markdown(sanitize_markdown(j["reflectionQuestions"]))
                        if j.get("aiSynthesis"):
                            st.markdown(sanitize_markdown(j["aiSynthesis"]))
                        st.markdown("---")
                        if j.get("tags"):
                            st.caption(f"🏷️ Теги: {', '.join(j.get('tags', []))}")

                        col_act1, col_act2 = st.columns(2)
                        with col_act1:
                            if st.button("✏️ Редактировать", key=f"btn_edit_{j_id}", use_container_width=True):
                                st.session_state.editing_journal_id = j_id
                                st.rerun()
                        with col_act2:
                            if st.button("🗑️ Удалить", key=f"btn_del_{j_id}", use_container_width=True, disabled=not bridge.is_active):
                                if bridge.delete_journal(j_id):
                                    st.success("🗑️ Запись удалена!")
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error("🔴 Не удалось удалить запись.")
        else:
            st.info(f"В журнале «{active_nb.get('title')}» пока нет записей. Создайте первую запись слева.")

    # ==================== ПОЛНОШИРИННАЯ СЕКЦИЯ: ИИ-ЦЕНТР РЕФЛЕКСИИ И СКВОЗНОГО СИНТЕЗА ====================
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown(f"### 🔮 ИИ-Центр Рефлексии и Сквозного Синтеза — `{active_nb.get('icon')} {active_nb.get('title')}`")
    st.caption("Глубокий доменный анализ отдельной записи или сквозной синтез всех записей Журнала в стиле Journal with Gemini")

    st.markdown("<div class='citadel-card'>", unsafe_allow_html=True)

    # 1. Режим Анализа
    analysis_mode = st.radio(
        "🎯 Режим ИИ-Анализа:",
        ["📌 Анализ ОДНОЙ записи (текущей из редактора или сохраненной)", f"🌐 Сквозной ИИ-Синтез ВСЕХ {len(active_journals)} записей Журнала «{active_nb.get('title')}»"],
        horizontal=True,
        key=f"analysis_mode_{active_nb['id']}"
    )

    selected_entry_text = ""
    if "📌" in analysis_mode:
        if active_journals:
            entry_opts = {}
            for j in active_journals:
                entry_opts[j["id"]] = f"📅 {j.get('date')} — {j.get('title')}"
            entry_opts["new"] = "✍️ Несохраненная запись из формы слева"

            sel_e = st.selectbox(
                "Выберите запись для анализа:",
                options=list(entry_opts.keys()),
                format_func=lambda x: entry_opts[x],
                key=f"sel_entry_{active_nb['id']}"
            )
            if sel_e == "new":
                selected_entry_text = st.session_state.get(f"new_content_{active_nb['id']}", "")
            else:
                for j in active_journals:
                    if j["id"] == sel_e:
                        selected_entry_text = f"Заголовок: {j.get('title')}\nДата: {j.get('date')}\nТекст:\n{j.get('content')}"
                        break
        else:
            selected_entry_text = st.session_state.get(f"new_content_{active_nb['id']}", "")

    # 2. Выбор ИИ-Модели и Провайдера
    col_prov, col_mod = st.columns([1, 2])
    with col_prov:
        ai_provider = st.selectbox("ИИ-Провайдер", ["Google Gemini", "Anthropic Claude", "Mistral AI"], key=f"ai_ref_prov_{active_nb['id']}")
    with col_mod:
        if ai_provider == "Google Gemini":
            avail_mods = list(DEFAULT_GEMINI_MODELS.keys())
            ai_model = st.selectbox("Модель ИИ", avail_mods, index=0, format_func=lambda x: DEFAULT_GEMINI_MODELS.get(x, x), key=f"ai_ref_mod_gem_{active_nb['id']}")
        elif ai_provider == "Anthropic Claude":
            avail_mods = list(DEFAULT_ANTHROPIC_MODELS.keys())
            ai_model = st.selectbox("Модель ИИ", avail_mods, index=5 if len(avail_mods)>5 else 0, format_func=lambda x: DEFAULT_ANTHROPIC_MODELS.get(x, x), key=f"ai_ref_mod_claude_{active_nb['id']}")
        elif ai_provider == "Mistral AI":
            avail_mods = list(DEFAULT_MISTRAL_MODELS.keys())
            ai_model = st.selectbox("Модель ИИ", avail_mods, index=0, format_func=lambda x: DEFAULT_MISTRAL_MODELS.get(x, x), key=f"ai_ref_mod_mistral_{active_nb['id']}")

    # 3. Доменные Шаблонные Вопросы в зависимости от Тематики Журнала
    cat_type = active_nb.get("categoryType", "GENERAL")

    if cat_type == "AI_WEBDEV":
        templates = [
            "💻 [Код & Архитектура]: Какие алгоритмы, стек и архитектурные решения в записи наиболее эффективны?",
            "🤖 [ИИ-Агенты & UX]: Как применение ИИ и интерфейса улучшило систему PIM и пользовательский опыт?",
            "⚡ [Оптимизация]: Какие 3 шага по рефакторингу и оптимизации кода следует сделать следующим шагом?",
            "🐛 [Анализ Ошибок]: Каков главный урок из возникших технических сложностей или багов?"
        ]
    elif cat_type == "MISSION":
        templates = [
            "🕊️ [Проявление Благодати]: Где в событиях записи явно видна рука Божья и духовные плоды?",
            "🌍 [Миссионерские Нужды]: Какие молитвенные нужды, люди и вызовы доверены Миссии в этой записи?",
            "🤝 [Единство и Победы]: Как укрепляется команда Миссии и какие духовные победы одержаны?",
            "📖 [Духовное Слово]: Какое откровение и Писание направляют служение Миссии Шехина?"
        ]
    elif cat_type == "SCHOOL_OF_CHRIST":
        templates = [
            "✝️ [Характер Христа]: Какую глубину характера Христова, смирения и любви открыл Дух Святой?",
            "📖 [Библейские Истины]: Какое место Писания и откровение коснулось сердца в этой записи?",
            "💡 [Ученичество]: В чем проявилось практическое послушание велению Господню?",
            "🕊️ [Трансформация Сердца]: Какие внутренние мотивы требуют очищения, Покаяния и молитвы?"
        ]
    elif cat_type == "FAMILY":
        templates = [
            "👨‍👩‍👧‍👦 [Семейный Мир]: За какие радости, покой и благодарности в доме я славлю Бога?",
            "❤️ [Любовь и Забота]: Как я проявил мудрость, доброту и заботу к близким сегодня?",
            "🌿 [Мир Души]: Какие личные переживания требуют Божьего умиротворения и поддержки?"
        ]
    elif cat_type == "THEOLOGY":
        templates = [
            "📜 [Доктринальный Анализ]: Какие библейские и теологические истины сформулированы в записи?",
            "🔍 [Академический Синтез]: Каковы параллели со Священным Писанием и выводы апологетики?"
        ]
    else: # GENERAL
        templates = [
            "🔮 [Комплексный анализ]: 3 глубоких назидательных вопроса для вечерней духовной рефлексии",
            "🕊️ [Благодарность]: В чем проявилось Божье присутствие и благословения сегодня?",
            "💡 [Урок Жизни]: Какой главный урок содержится в этих событиях?"
        ]

    templates.append("✍️ [Свой Произвольный Вопрос]: Ввести собственный вопрос ниже...")

    sel_template = st.selectbox("🎯 Выберите Шаблонный Вопрос или укажите свой:", templates, key=f"sel_template_{active_nb['id']}")

    custom_question = ""
    if "✍️" in sel_template:
        custom_question = st.text_input("✍️ Введите Ваш уникальный вопрос к ИИ-Оракулу:", placeholder="Например: Сформируй молитву и вывод по этой записи...", key=f"custom_q_{active_nb['id']}")

    if st.button("🚀 Сгенерировать ИИ-Рефлексию и Синтез", type="primary", use_container_width=True):
        # Формируем текст контекста
        if "🌐" in analysis_mode:
            if not active_journals:
                st.warning("В текущем журнале нет сохраненных записей для сквозного анализа.")
                st.stop()
            context_text = f"АРХИВ ВСЕХ ЗАПИСЕЙ ЖУРНАЛА «{active_nb.get('title')}» ({len(active_journals)} записей):\n\n"
            for idx, j in enumerate(active_journals, 1):
                context_text += f"--- Запись #{idx} ({j.get('date')}) ---\nЗаголовок: {j.get('title')}\nТекст:\n{j.get('content')}\n\n"
        else:
            if not selected_entry_text or not selected_entry_text.strip():
                st.warning("Введите текст записи или выберите сохраненную запись из списка.")
                st.stop()
            context_text = f"ЗАПИСЬ ЖУРНАЛА «{active_nb.get('title')}»:\n\n{selected_entry_text}"

        # Формируем вопрос
        if "✍️" in sel_template:
            final_q = custom_question if custom_question.strip() else "Сформируй глубокий духовный вывод и вопросы по этой записи."
        else:
            final_q = sel_template

        prompt = (
            f"Ты — Персональный ИИ-Оракул и Ведущий Аналитик Цитадели Духа («Shekinah Cloud»). "
            f"Проанализируй предоставленные материалы Журнала «{active_nb.get('title')}» ({active_nb.get('description')}).\n\n"
            f"ЗАПРОС И ВОПРОС ПОЛЬЗОВАТЕЛЯ:\n{final_q}\n\n"
            f"КОНТЕКСТ ЖУРНАЛА:\n{context_text}\n\n"
            f"ТРЕБОВАНИЯ К ОТВЕТУ:\n"
            f"1. Ответ должен быть выведен в БОГАТОМ, ВЕЛИКОЛЕПНОМ формате Markdown с эмодзи, иконками, выделением ключевых мыслей и цитатами.\n"
            f"2. Дай глубокий, академичный, духовно назидательный и практический ответ во всю ширину экрана.\n"
            f"3. Подведи 3 конкретных ключевых вывода (Takeaways) и сформулируй молитву или напутствие."
        )

        with st.spinner(f"⏳ {ai_provider} ({ai_model}) выполняет глубокий анализ..."):
            try:
                if ai_provider == "Google Gemini":
                    ai_res = gemini_client.ask_gemini(prompt, model_name=ai_model)
                elif ai_provider == "Anthropic Claude":
                    ai_res = anthropic_client.ask_anthropic(prompt, model_name=ai_model)
                elif ai_provider == "Mistral AI":
                    ai_res = mistral_client.ask_mistral(prompt, model_name=ai_model)
                else:
                    ai_res = gemini_client.ask_gemini(prompt)

                # Автоматически добавляем сигнатуру модели
                sig_block = get_model_signature_block(ai_model, ai_provider)
                if sig_block not in ai_res:
                    ai_res += sig_block

                st.session_state[f"ai_journal_res_{active_nb['id']}"] = ai_res
                st.success(f"✅ ИИ-Рефлексия успешно сгенерирована моделью {ai_model}!")
            except Exception as e:
                st.error(f"🔴 Ошибка при генерации ИИ-ответа: {str(e)}")

    # Вывод результата генерации во всю ширину
    saved_ai_res = st.session_state.get(f"ai_journal_res_{active_nb['id']}", "")
    if saved_ai_res:
        clean_ai_res = sanitize_markdown(saved_ai_res)
        st.markdown("---")
        st.markdown("#### 📜 Результат ИИ-Анализа и Духовной Рефлексии:")
        st.markdown("<div style='background: rgba(17, 24, 39, 0.85); padding: 25px; border-radius: 12px; border: 1px solid rgba(147, 51, 234, 0.4); box-shadow: 0 4px 20px rgba(0,0,0,0.4);'>", unsafe_allow_html=True)
        st.markdown(clean_ai_res)
        st.markdown("</div>", unsafe_allow_html=True)

        col_act_copy, col_act_clear = st.columns([3, 1])
        with col_act_copy:
            render_copy_expander(clean_ai_res, "📋 Скопировать ИИ-Рефлексию в буфер обмена")
        with col_act_clear:
            if st.button("🗑️ Очистить ответ ИИ", key=f"clear_ai_res_{active_nb['id']}", use_container_width=True):
                st.session_state[f"ai_journal_res_{active_nb['id']}"] = ""
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ==================== РАЗДЕЛ 3: ПРОЕКТЫ ====================
elif active_tab == "📁 Проекты":
    st.markdown("<h2 class='citadel-header'>📁 Управление Проектами</h2>", unsafe_allow_html=True)
    projects = bridge.load_projects() if bridge.is_active else []
    with st.expander("➕ Создать новый проект", expanded=not projects):
        render_record_editor(
            "project",
            {"title": "", "description": "", "milestones": "", "category": "Ministry", "status": "Planning", "tags": []},
            projects,
            [],
            "create_project",
            creating=True,
        )

    st.markdown("---")
    if projects:
        st.markdown(f"### 📁 Проекты ({len(projects)})")
        for project in projects:
            project_id = project.get("id", "")
            with st.expander(f"📁 {project.get('title', 'Без названия')} · {project.get('status', 'Active')}"):
                if st.session_state.get("editing_project_id") == project_id:
                    render_record_editor("project", project, projects, [], f"edit_project_{project_id}")
                else:
                    st.caption(f"{project.get('category', '—')} · {project.get('startDate') or 'без даты начала'} — {project.get('endDate') or 'без даты окончания'}")
                    st.markdown(sanitize_markdown(project.get("description", "")))
                    if project.get("milestones"):
                        st.markdown("#### Этапы")
                        st.markdown(sanitize_markdown(project["milestones"]))
                    if project.get("tags"):
                        st.caption("🏷️ " + ", ".join(project["tags"]))
                    edit_col, delete_col = st.columns(2)
                    with edit_col:
                        if st.button("✏️ Редактировать свойства", key=f"edit_project_{project_id}"):
                            st.session_state.editing_project_id = project_id
                            st.rerun()
                    with delete_col:
                        if st.button("🗑️ Удалить проект", key=f"delete_project_{project_id}", disabled=not bridge.is_active):
                            if bridge.delete_project(project_id):
                                st.rerun()
                            else:
                                st.error("🔴 Не удалось удалить проект.")
    else:
        st.info("Проекты пока не добавлены.")

# ==================== РАЗДЕЛ 4: ЗАМЕТКИ ====================
elif active_tab == "📝 Заметки":
    st.markdown("<h2 class='citadel-header'>📝 Заметки & База Знаний</h2>", unsafe_allow_html=True)
    projects = bridge.load_projects() if bridge.is_active else []
    notes = bridge.load_notes() if bridge.is_active else []
    with st.expander("➕ Создать заметку", expanded=not notes):
        render_record_editor(
            "note",
            {"title": "", "category": "General", "content": "", "tags": [], "isArchived": False},
            projects,
            [],
            "create_note",
            creating=True,
        )

    st.markdown("### 📚 Моя база знаний")
    if notes:
        for note in notes:
            note_id = note.get("id", "")
            with st.expander(f"📌 [{note.get('category', 'General')}] {note.get('title', 'Без названия')}"):
                if st.session_state.get("editing_note_id") == note_id:
                    render_record_editor("note", note, projects, [], f"edit_note_{note_id}")
                else:
                    if note.get("projectId"):
                        project_title = next(
                            (project.get("title") for project in projects if project.get("id") == note["projectId"]),
                            "Проект не найден",
                        )
                        st.caption(f"📁 {project_title}")
                    st.caption(f"Временная шкала: {note.get('startDate') or '—'} — {note.get('endDate') or '—'}")
                    st.markdown(sanitize_markdown(note.get("content", "")))
                    if note.get("tags"):
                        st.caption("🏷️ " + ", ".join(note["tags"]))
                    edit_col, delete_col = st.columns(2)
                    with edit_col:
                        if st.button("✏️ Редактировать все свойства", key=f"edit_note_btn_{note_id}"):
                            st.session_state.editing_note_id = note_id
                            st.rerun()
                    with delete_col:
                        if st.button("🗑️ Удалить заметку", key=f"delete_note_{note_id}", disabled=not bridge.is_active):
                            if bridge.delete_note(note_id):
                                st.rerun()
                            else:
                                st.error("🔴 Не удалось удалить заметку.")
    else:
        st.info("Заметки отсутствуют.")

# ==================== РАЗДЕЛ 5: КАЛЕНДАРЬ ====================
elif active_tab == "📅 Календарь":
    st.markdown("<h2 class='citadel-header'>📅 Интерактивный календарь Цитадели</h2>", unsafe_allow_html=True)
    st.caption("Подсвеченные дни содержат записи или входят в их временную шкалу. Выберите день, чтобы просмотреть, изменить или создать запись.")

    if bridge.is_active:
        calendar_projects = bridge.load_projects()
        calendar_notebooks = bridge.load_notebooks()
        calendar_records = [
            ("Журнал", "journal", bridge.load_journals()),
            ("Заметки", "note", bridge.load_notes()),
            ("Задачи", "task", bridge.load_tasks()),
            ("Проекты", "project", calendar_projects),
            ("Сейф", "vault", bridge.load_vault()),
        ]
        today = date.today()
        if "calendar_month" not in st.session_state:
            st.session_state.calendar_month = date(today.year, today.month, 1)
        if "calendar_selected_date" not in st.session_state:
            st.session_state.calendar_selected_date = today

        month_start = st.session_state.calendar_month
        previous_col, title_col, next_col = st.columns([1, 4, 1])
        with previous_col:
            if st.button("← Предыдущий", key="calendar_previous"):
                year, month = (month_start.year - 1, 12) if month_start.month == 1 else (month_start.year, month_start.month - 1)
                st.session_state.calendar_month = date(year, month, 1)
                st.session_state.calendar_selected_date = date(year, month, 1)
                st.rerun()
        with title_col:
            month_names = [
                "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
            ]
            st.markdown(f"<h3 style='text-align:center'>{month_names[month_start.month - 1]} {month_start.year}</h3>", unsafe_allow_html=True)
        with next_col:
            if st.button("Следующий →", key="calendar_next"):
                year, month = (month_start.year + 1, 1) if month_start.month == 12 else (month_start.year, month_start.month + 1)
                st.session_state.calendar_month = date(year, month, 1)
                st.session_state.calendar_selected_date = date(year, month, 1)
                st.rerun()

        with st.container(key="calendar-grid"):
            weekday_columns = st.columns(7)
            for column, weekday in zip(weekday_columns, ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")):
                column.markdown(f"**{weekday}**")
            for week_index, week in enumerate(month_calendar.monthcalendar(month_start.year, month_start.month)):
                day_columns = st.columns(7)
                for column, day_number in zip(day_columns, week):
                    if day_number == 0:
                        column.write("")
                        continue
                    calendar_day = date(month_start.year, month_start.month, day_number)
                    matching = [
                        record
                        for _, record_type, records in calendar_records
                        for record in records
                        if record_matches_date(record_type, record, calendar_day)
                    ]
                    is_selected = st.session_state.calendar_selected_date == calendar_day
                    marker = f" · {len(matching)}" if matching else ""
                    label = f"{'▶ ' if is_selected else ''}{day_number}{marker}"
                    if column.button(
                        label,
                        key=f"calendar_day_{month_start.year}_{month_start.month}_{day_number}_{week_index}",
                        type="primary" if matching else "secondary",
                        use_container_width=True,
                        help=f"{len(matching)} записей" if matching else "Нет записей",
                    ):
                        st.session_state.calendar_selected_date = calendar_day
                        st.rerun()

        selected_date = st.session_state.calendar_selected_date
        st.markdown(f"### 📌 Записи за {selected_date.strftime('%d.%m.%Y')}")
        selected_records = [
            (section, record_type, record)
            for section, record_type, records in calendar_records
            for record in records
            if record_matches_date(record_type, record, selected_date)
        ]
        if selected_records:
            for section, record_type, record in selected_records:
                record_id = str(record.get("id", ""))
                editor_key = (record_type, record_id)
                with st.expander(f"{section} · {record.get('title', 'Без названия')}"):
                    if st.session_state.get("calendar_editing_record") == editor_key:
                        render_record_editor(
                            record_type,
                            record,
                            calendar_projects,
                            calendar_notebooks,
                            f"calendar_edit_{record_type}_{record_id}",
                            default_date=selected_date,
                            master_passphrase=st.session_state.get("master_passphrase", ""),
                        )
                    else:
                        st.caption(
                            f"Временная шкала: {record.get('startDate') or '—'} — {record.get('endDate') or '—'}"
                        )
                        if record.get("projectId"):
                            linked_project = next(
                                (project.get("title") for project in calendar_projects if project.get("id") == record["projectId"]),
                                "Проект не найден",
                            )
                            st.caption(f"📁 Проект: {linked_project}")
                        if record.get("tags"):
                            st.caption("🏷️ " + ", ".join(record["tags"]))
                        if record_type == "journal":
                            st.caption(f"📓 {record.get('category') or 'Журнал'} · {record.get('date', '')}")
                            st.markdown(sanitize_markdown(record.get("content", "")))
                            for extra in ("reflectionQuestions", "aiSynthesis"):
                                if record.get(extra):
                                    st.markdown(sanitize_markdown(record[extra]))
                        elif record_type == "project":
                            st.caption(f"{record.get('category', '—')} · {record.get('status', '—')}")
                            st.markdown(sanitize_markdown(record.get("description", "")))
                            if record.get("milestones"):
                                st.markdown(sanitize_markdown(record["milestones"]))
                        elif record_type == "vault":
                            st.info("🔒 Содержимое секрета не отображается в календаре.")
                            if record.get("note"):
                                st.markdown(sanitize_markdown(record["note"]))
                        else:
                            st.markdown(sanitize_markdown(record.get("content", record.get("description", ""))))

                        edit_col, delete_col = st.columns(2)
                        with edit_col:
                            if st.button("✏️ Редактировать с предпросмотром", key=f"calendar_edit_btn_{record_type}_{record_id}"):
                                st.session_state.calendar_editing_record = editor_key
                                st.rerun()
                        with delete_col:
                            if st.button("🗑️ Удалить запись", key=f"calendar_delete_{record_type}_{record_id}", disabled=not bridge.is_active):
                                delete_methods = {
                                    "journal": bridge.delete_journal,
                                    "note": bridge.delete_note,
                                    "task": bridge.delete_task,
                                    "project": bridge.delete_project,
                                    "vault": bridge.delete_vault_entry,
                                }
                                if delete_methods[record_type](record_id):
                                    st.session_state.calendar_editing_record = None
                                    st.rerun()
                                else:
                                    st.error("🔴 Не удалось удалить запись.")
        else:
            st.info("На выбранную дату записей нет.")

        create_types = {
            "Журнал": "journal",
            "Заметка": "note",
            "Задача": "task",
            "Проект": "project",
            "Секрет Сейфа": "vault",
        }
        with st.expander("➕ Создать запись для выбранной даты", expanded=False):
            selected_type = st.selectbox("Раздел записи", list(create_types), key="calendar_create_type")
            record_type = create_types[selected_type]
            default_record: Dict[str, Any] = {"title": ""}
            if record_type == "journal":
                default_record.update({
                    "notebookId": calendar_notebooks[0].get("id", "") if calendar_notebooks else "",
                    "date": str(selected_date),
                    "category": calendar_notebooks[0].get("title", "Журнал") if calendar_notebooks else "Журнал",
                    "content": "",
                    "tags": [],
                })
            elif record_type == "note":
                default_record.update({"category": "General", "content": "", "tags": [], "isArchived": False})
            elif record_type == "task":
                default_record.update({"category": "Личное", "description": ""})
            elif record_type == "project":
                default_record.update({"category": "Ministry", "status": "Planning", "description": "", "milestones": "", "tags": []})
            else:
                default_record.update({"secretType": "API_KEY", "serviceName": "", "note": ""})
            render_record_editor(
                record_type,
                default_record,
                calendar_projects,
                calendar_notebooks,
                f"calendar_create_{record_type}",
                creating=True,
                default_date=selected_date,
                master_passphrase=st.session_state.get("master_passphrase", ""),
            )
    else:
        st.info("Подключитесь к облачному хранилищу, чтобы просматривать и создавать записи в календаре.")

# ==================== РАЗДЕЛ 6: ЗАДАЧИ ====================
elif active_tab == "📋 Задачи":
    st.markdown("<h2 class='citadel-header'>📋 Управление Задачами</h2>", unsafe_allow_html=True)
    st.caption("Прикрепление к проектам, сроки и контроль выполнения")
    all_projects = bridge.load_projects() if bridge.is_active else []
    tasks = bridge.load_tasks() if bridge.is_active else []
    with st.expander("➕ Создать задачу", expanded=not tasks):
        render_record_editor(
            "task",
            {"title": "", "description": "", "category": "Личное"},
            all_projects,
            [],
            "create_task",
            creating=True,
        )

    if tasks:
        st.markdown(f"### 📝 Мои задачи ({len(tasks)})")
        for task in tasks:
            task_id = task.get("id", "")
            with st.expander(f"📋 {task.get('title', 'Без названия')} · {task.get('category', 'Личное')}"):
                if st.session_state.get("editing_task_id") == task_id:
                    render_record_editor("task", task, all_projects, [], f"edit_task_{task_id}")
                else:
                    st.caption(f"{task.get('startDate') or 'без даты начала'} — {task.get('endDate') or 'без даты окончания'}")
                    st.markdown(sanitize_markdown(task.get("description", "")))
                    if task.get("projectId"):
                        project_title = next(
                            (project.get("title") for project in all_projects if project.get("id") == task["projectId"]),
                            "Проект не найден",
                        )
                        st.caption(f"📁 {project_title}")
                    edit_col, delete_col = st.columns(2)
                    with edit_col:
                        if st.button("✏️ Редактировать", key=f"edit_task_btn_{task_id}"):
                            st.session_state.editing_task_id = task_id
                            st.rerun()
                    with delete_col:
                        if st.button("🗑️ Удалить", key=f"delete_task_{task_id}", disabled=not bridge.is_active):
                            if bridge.delete_task(task_id):
                                st.rerun()
                            else:
                                st.error("🔴 Не удалось удалить задачу.")
    else:
        st.info("Задач пока нет. Создайте первую запись выше.")

# ==================== РАЗДЕЛ 7: СЕЙФ КЛЮЧЕЙ ====================
elif active_tab == "🔐 Сейф Ключей":
    st.markdown("<h2 class='citadel-header'>🔐 Зашифрованный Сейф Ключей и Паролей</h2>", unsafe_allow_html=True)
    st.caption("Значение секрета остаётся зашифрованным; предпросмотр показывает только публичные заметки.")
    master_pass = st.session_state.get("master_passphrase", "")
    projects = bridge.load_projects() if bridge.is_active else []
    vault_entries = bridge.load_vault() if bridge.is_active else []
    with st.expander("➕ Добавить секрет в Сейф"):
        render_record_editor(
            "vault",
            {"title": "", "secretType": "API_KEY", "serviceName": "", "note": ""},
            projects,
            [],
            "create_vault",
            creating=True,
            master_passphrase=master_pass,
        )

    st.markdown("### 🔑 Хранимые Секреты")
    if vault_entries:
        for ve in vault_entries:
            entry_id = ve.get("id", "")
            with st.expander(f"🛡️ {ve.get('title', 'Секрет')} · {ve.get('secretType', 'OTHER')}"):
                if st.session_state.get("editing_vault_id") == entry_id:
                    render_record_editor(
                        "vault",
                        ve,
                        projects,
                        [],
                        f"edit_vault_{entry_id}",
                        master_passphrase=master_pass,
                    )
                else:
                    st.caption(f"🌐 {ve.get('serviceName') or 'Сервис не указан'}")
                    if ve.get("note"):
                        st.markdown(sanitize_markdown(ve["note"]))
                    st.caption(f"📅 {ve.get('startDate') or '—'} — {ve.get('endDate') or '—'}")
                    if ve.get("projectId"):
                        project_title = next(
                            (project.get("title") for project in projects if project.get("id") == ve["projectId"]),
                            "Проект не найден",
                        )
                        st.caption(f"📁 {project_title}")
                    show_key = st.checkbox("👁️ Показать значение", key=f"show_{entry_id}")
                    if show_key:
                        try:
                            decrypted = decrypt_secret(ve.get("encryptedPayload", ""), master_pass)
                        except Exception as error:
                            st.error(f"🔴 Не удалось расшифровать секрет: {error}")
                        else:
                            st.code(decrypted)
                    else:
                        st.code("••••••••••••••••••••••••••••••••••••••••••••••••")
                    edit_col, delete_col = st.columns(2)
                    with edit_col:
                        if st.button("✏️ Редактировать свойства", key=f"edit_vault_{entry_id}"):
                            st.session_state.editing_vault_id = entry_id
                            st.rerun()
                    with delete_col:
                        if st.button("🗑️ Удалить", key=f"delete_vault_{entry_id}", disabled=not bridge.is_active):
                            if bridge.delete_vault_entry(entry_id):
                                st.rerun()
                            else:
                                st.error("🔴 Не удалось удалить запись Сейфа.")
    else:
        st.info("В Сейфе пока нет записей.")

# ==================== РАЗДЕЛ 6: НАСТРОЙКИ ====================
elif active_tab == "🏛️ Настройки":
    st.markdown("<h2 class='citadel-header'>🏛️ Настройки Ордена Цитадели</h2>", unsafe_allow_html=True)
    st.markdown("🔐 Секреты авторизации и API-ключи не отображаются в интерфейсе.")
    if bridge.is_active:
        st.success("Защищённое облачное хранилище настроено.")
    else:
        st.error("Облачное хранилище не настроено. Данные не будут сохраняться.")

if bridge.last_error:
    st.error(
        "🔴 Не удалось получить данные из облачного хранилища. "
        "Записи не удалены; проверьте секрет шлюза и подключение."
    )
