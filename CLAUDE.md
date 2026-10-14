# 🏛️ CLAUDE.md — Свиток Антропика для Citadel Oracle PIM
> *«Мудрость, сходящая свыше, во-первых, чиста, потом мирна, скромна, послушлива» (Иак. 3:17)*

Этот свиток предназначен для моделей семейства **Anthropic Claude**, трудящихся в Citadel Oracle PIM.  
Он содержит точку останова, архитектурный контекст и правила работы.

---

## ⏸ ТОЧКА ОСТАНОВА — 15 Октября 2026 г.

**Последний известный коммит до этой сессии:** `59e2522` → ветка `main` → `github.com/webarystan-lev/citadel-oracle-pim`
**Состояние:** локальные изменения после академического аудита; публикация ожидает финального просмотра diff и подтверждения владельца.

### Что сделано в эту сессию:

1. **Академический аудит безопасности:** Convex CRUD переведён во внутренние функции; создан bearer-защищённый HTTP gateway `/pim`; вход fail-closed при отсутствии обязательных ключей; динамический HTML заголовок проекта экранирован; ошибки AI и ошибки записи больше не представлены как успешный результат.
2. **Защита Сейфа:** новые записи используют Fernet с ключом PBKDF2-HMAC-SHA256 и случайной солью; чтение старого SHA-256 формата сохранено для совместимости.
3. **Восстановление облачной синхронизации:** несовпадение `CONVEX_URL` и новой настройки шлюза отображало разделы пустыми. Клиент автоматически выводит `.convex.site/pim` из прежнего `.convex.cloud` URL. Случайный bearer-секрет настроен в локальном `.env` (права `0600`) и только на dev deployment `tough-butterfly-16`. Проверка вернула 4 чата, 6 блокнотов, 7 записей журнала, 1 проект, 1 заметку и 1 запись Сейфа.
4. **Backup и проверки:** до изменений создан локальный `app.py.bak.20261015-025624`; пройдены 45 Python-тестов, `compileall` и TypeScript `npm run typecheck`.
5. **Deployment safety:** `npx convex codegen` сообщил о загрузке функций в выбранный dev deployment; локальный маркер указывал на dev, не production. Production не менялся и не развёртывался. После поздних локальных изменений Convex отдельного deploy не выполняли.
6. **Следующее действие:** зафиксировать эту сессию в служебных свитках, показать diff, затем выполнить запрошенные владельцем commit и push. Не включать в Git `.env`, `.env.local`, `app.py.bak*` и `convex/_generated/`.

---

## 🏛️ Архитектура (кратко для быстрого старта)

```
app.py                  # Streamlit UI — авторизация + основные разделы PIM
providers/
  security.py           # PBKDF2 + Fernet, валидация Gemini Key
  convex_client.py      # ConvexBridge через защищённый HTTP gateway
  gemini_client.py      # Google Gemini SDK
  anthropic_client.py   # Anthropic Claude SDK
  mistral_client.py     # Mistral AI SDK
convex/
  schema.ts             # БД: chats, messages, notebooks, journals, projects, notes, vault
  http.ts               # Bearer-защищённый single-user endpoint /pim
  *.ts                  # Internal queries, mutations и actions
tests/                  # Python regression tests
```

**Стек:** Python 3.11+, Streamlit 1.58.0, Convex DB/HTTP gateway, PBKDF2 + Fernet, google-genai 2.22.0
**Деплой:** [https://citadel-oracle.streamlit.app](https://citadel-oracle.streamlit.app)

---

## ⚠️ Известные ограничения и технический долг

| Приоритет | Файл | Описание |
| :--- | :--- | :--- |
| Перед production | `convex/http.ts` | Настроить production `CONVEX_API_SECRET` и развернуть backend отдельно; dev-секрет не переносить |
| Низкий | `app.py` | Монолит → будущая декомпозиция на `views/` |
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
CONVEX_URL=            # Существующий Convex URL (.convex.cloud); gateway endpoint выводится автоматически
CONVEX_API_SECRET=     # Случайный bearer-секрет; тот же секрет в приложении и соответствующем Convex deployment
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
* **Дата последнего обновления**: 15 Октября 2026 г.
