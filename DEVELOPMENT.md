# 🛠️ Руководство по Разработке — Citadel Oracle PIM

> *«Устрой пути свои пред Господом, и помыслы твои совершатся» (Притчи 16:3)*

Этот священный документ содержит технические подробности устройства архитектуры, инструкции по обслуживанию базы данных Convex DB, шифрованию AES-256 Fernet и добавлению новых функций в **The Spirit of the Shekinah Citadel Oracle (Shekinah Citadel Oracle PIM)**.

---

## 🏛️ Архитектура Проекта

```
citadel-oracle-pim/
├── .agents/                # Настройки, навыки и правила для Antigravity 2.0 & IDE
│   ├── rules/              # Правила выполнения кода
│   └── skills/             # Специализированные навыки агентов (convex-advisor, oracle-pim, etc.)
├── .env                    # Секретные ключи API, CONVEX_URL, PIM_SECRET_KEY
├── .envrc                  # direnv конфигурация для автоактивации .venv
├── .venv/                  # Изолированное виртуальное окружение Python
├── app.py                  # Главное Streamlit-приложение (Gatekeeper + Авторизация + Все 6 Модулей)
├── requirements.txt        # Версии зависимостей Python (google-genai==2.22.0, streamlit==1.58.0, convex==0.7.0)
├── package.json            # npm конфигурация Convex DB
├── convex/                 # TypeScript бэкенд Convex DB
│   ├── schema.ts           # Расширенная схема PIM (chats, messages, notebooks, journals, projects, notes, vault)
│   ├── chats.ts            # Обработчики диалогов
│   ├── messages.ts         # Обработчики сообщений
│   ├── notebooks.ts        # Обработчики тематических журналов/блокнотов
│   ├── journals.ts         # Обработчики дневниковых записей
│   ├── projects.ts         # Обработчики проектов
│   ├── notes.ts            # Обработчики заметок & базы знаний
│   └── vault.ts            # Обработчики зашифрованного сейфа
└── providers/              # Провайдеры API и сервис безопасности
    ├── security.py         # Шифрование AES-256 (Fernet) и Валидация Gemini API Key
    ├── convex_client.py    # Python ConvexBridge для синхронизации с Convex Cloud
    ├── gemini_client.py    # Клиент Google Gemini (google-genai SDK)
    ├── anthropic_client.py # Клиент Anthropic Claude
    └── mistral_client.py   # Клиент Mistral AI
```

---

## 🔐 Шифрование и Безопасность (Security Service)

Модуль `providers/security.py` отвечает за два уровня защиты:
1. **`verify_gemini_api_key(api_key)`**: Выполняет официальный вызов `genai.list_models()` к Google Gemini API для валидации ключа при входе в систему Gatekeeper.
2. **`encrypt_secret(plain_text, passphrase)` & `decrypt_secret(encrypted_text, passphrase)`**: Выполняет хэширование SHA-256 мастер-пароля для генерации 256-битного Fernet-ключа и зашифровывает данные Сейфа перед отправкой в Convex DB.

---

## 📖 Мульти-Журнальная Архитектура (Multi-Journal System)

В модуле `📖 Журнал` реализована концепция тематических журналов (*Journal with Gemini*):
1. **Таблица `notebooks` в Convex DB**: Хранит категории/блокноты (`title`, `description`, `icon`, `categoryType`).
2. **Таблица `journals` в Convex DB**: Связана с `notebooks` через новое поле `notebookId` и индекс `by_notebookId`.
3. **Узкопрофильные ИИ-вопросы**: Каждая категория (`AI_WEBDEV`, `MISSION`, `SCHOOL_OF_CHRIST`, `FAMILY`, `THEOLOGY`, `GENERAL`) загружает доменные шаблонные вопросы.
4. **Сквозной ИИ-Синтез**: Поддерживается сканирование и рефлексия как одной записи, так и всех записей выбранного журнала во всю ширину экрана.

---

## 🗄️ База Данных Convex DB

Схема базы зафиксирована в `convex/schema.ts`:
* `chats` — Таблица настроек диалогов
* `messages` — История сообщений
* `notebooks` — Тематические журналы/блокноты
* `journals` — Ежедневные записи журналов с привязкой к `notebookId` и `projectId`
* `projects` — Проекты, категории и milestones
* `notes` — База знаний и заметки
* `vault` — Зашифрованные записи сейфа

Для применения новой схемы в облаке Convex выполняйте:
```bash
npx convex dev --once   # Для среды разработки
npx convex deploy       # Для боевой среды (Production)
```

> **Архитектурный дуализм версий Convex**:
> * **Python Слой (`convex==0.7.0`)**: клиентский мост (`ConvexBridge` в `providers/convex_client.py`) для вызова мутаций и запросов из Streamlit.
> * **Node.js/TypeScript Слой (`convex ^1.42.1`)**: серверная часть в каталоге `convex/` (`schema.ts`, обработчики) и CLI-инструментарий разработчика.

---

## 🔮 Перспективный План Развития (Future Roadmap)

По итогам соборного аудита экспертов (**NVIDIA Nemotron 3 Ultra** — 9.5/10 и **Mistral Medium 3.5** — 9.7/10), монолитный файл `app.py` и текущая архитектура признаны образцовыми и надежными в работе. На будущее при расширении функционала запланировано:
1. **Модульная декомпозиция представлений**: выделение отдельных представлений (`views/chat.py`, `views/journal.py`, `views/projects.py`, `views/notes.py`, `views/vault.py`) при сохранении единого роутера в `app.py`.
2. **Вынос CSS-стилей**: перемещение `CITADEL_CSS` в статический ассет `assets/citadel.css` с подгрузкой через `st.html`.
3. **Расширение провайдеров**: интеграция дополнительных ИИ-шлюзов по мере необходимости.

---

## ⚡ Antigravity 2.0 Integration & Subagents

В проекте активны интеграционные навыки для Antigravity 2.0:
* Навык `oracle-pim` (`.agents/skills/oracle-pim/SKILL.md`) контролирует операции над Convex DB, шифрование Сейфа и тестирование Streamlit.
* Навыки Convex (`convex-advisor`, `convex-reviewer`, `convex-expert`) обеспечивают регулярный аудит и отладку схемы.
