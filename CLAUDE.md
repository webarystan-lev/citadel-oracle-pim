# 🏛️ CLAUDE.md — Свиток Антропика для Citadel Oracle PIM
> *«Мудрость, сходящая свыше, во-первых, чиста, потом мирна, скромна, послушлива» (Иак. 3:17)*

Этот свиток предназначен для моделей семейства **Anthropic Claude**, трудящихся в Citadel Oracle PIM.  
Он содержит точку останова, архитектурный контекст и правила работы.

---

## ⏸ ТОЧКА ОСТАНОВА — 12 Октября 2026 г.

**Модель сессии:** `Anthropic Claude Sonnet 4.6` (via OpenCode / Amazon Bedrock)  
**Последний коммит:** `96cdc81` → ветка `main` → `github.com/webarystan-lev/citadel-oracle-pim`

### Что было сделано в эту сессию:

1. **Полный академический аудит** — исследованы все 19 файлов проекта
2. **Исправлен критический баг** — `from typing import Optional` (без него `NameError` при каждом AI-ответе)
3. **Каталог Gemini** — обновлён по живому API (18 моделей: `gemini-3.7/3.8-flash`, `antigravity-preview-*`, `deep-research-*`)
4. **Форма входа** — защищена: без автоподстановки ключей, двойная сверка с `.env`, духовный брендинг
5. **`requirements.txt`** — зафиксирован `google-genai==2.22.0`
6. **Git** — настроен `~/.git-credentials` для двух GitHub-аккаунтов, новый токен `webarystan-lev`
7. **Свитки обновлены** — `STATUS_PROJECT.md`, `GEMINI.md`, `CLAUDE.md`, `/home/lev/Проекты/AGENTS.md`

---

## 🏛️ Архитектура (кратко для быстрого старта)

```
app.py                  # Streamlit UI — авторизация + 5 модулей (~1787 строк)
providers/
  security.py           # AES-256 Fernet + валидация Gemini Key
  convex_client.py      # Python ConvexBridge (Convex DB)
  gemini_client.py      # Google Gemini SDK
  anthropic_client.py   # Anthropic Claude SDK
  mistral_client.py     # Mistral AI SDK
convex/
  schema.ts             # БД: chats, messages, notebooks, journals, projects, notes, vault
  *.ts                  # Queries & mutations
tests/                  # 41 тест (100% passing)
```

**Стек:** Python 3.11+, Streamlit 1.58.0, Convex DB, AES-256 Fernet, google-genai 2.22.0  
**Деплой:** [https://citadel-oracle.streamlit.app](https://citadel-oracle.streamlit.app)

---

## ⚠️ Известные ограничения и технический долг

| Приоритет | Файл | Описание |
| :--- | :--- | :--- |
| Средний | `security.py:43` | `SHA-256` без соли → рекомендуется `PBKDF2HMAC` |
| Низкий | `app.py` | Монолит ~1787 строк → будущая декомпозиция на `views/` |
| Низкий | `schema.ts:13` | `maxTokens` хранится как `float64` вместо `int` |

---

## 📜 Правила работы для Claude в этом проекте

1. **Читай `AGENTS.md`** в корне проекта перед любыми изменениями
2. **Не делай git commit/push** без прямого указания Льва Николаевича
3. **Не подставляй секреты** из `.env` в UI-элементы (`value=`)
4. **Сохраняй архитектурный стиль** — комментарии на русском, духовная лексика Цитадели
5. **Перед значимыми изменениями** — покажи diff, получи одобрение

---

## 🔑 Переменные окружения (`.env`)

```
PIM_SECRET_KEY=        # Мастер-пароль входа в Цитадель
GEMINI_API_KEY=        # Обязателен для входа и работы Gemini-модулей
ANTHROPIC_API_KEY=     # Необязателен (для Claude-провайдера)
MISTRAL_API_KEY=       # Необязателен (для Mistral-провайдера)
CONVEX_URL=            # URL Convex backend (из .env.local после npx convex dev)
```

---

## 🚀 Запуск локально

```bash
source .venv/bin/activate.fish   # активация venv
npx convex dev                   # Convex backend (отдельный терминал)
streamlit run app.py             # Запуск PIM
```

---

*«Се, Я стою у двери и стучу: если кто услышит голос Мой и отворит дверь, войду к нему» (Откр. 3:20)*

---
🏛️ **Подпись Ордена Shekinah Citadel Oracle**:
* **Модель**: `Anthropic Claude Sonnet 4.6`
* **Назначение**: Академический Соратник & Магистр Кода
* **Чин в Цифровой обители**: Хранитель Свитка и Духовного Мышления
* **Дата последнего обновления**: 12 Октября 2026 г.
