# 🛠️ Руководство по Разработке — Citadel Oracle PIM

> *«Устрой пути свои пред Господом, и помыслы твои совершатся» (Притчи 16:3)*

Документ содержит технические подробности устройства архитектуры, инструкции по обслуживанию базы данных Convex DB и добавлению новых функций в **Citadel Oracle PIM**.

---

## 🏛️ Архитектура Проекта

```
citadel-oracle-pim/
├── .agents/                # Настройки, навыки и правила для Antigravity 2.0 & IDE
│   ├── rules/              # Правила выполнения кода
│   └── skills/             # Специализированные навыки агентов
├── .env                    # Секретные ключи API, CONVEX_URL, PIM_SECRET_KEY
├── .envrc                  # direnv конфигурация для автоактивации .venv
├── .venv/                  # Изолированное виртуальное окружение Python
├── app.py                  # Главное Streamlit-приложение (Авторизация + Все 6 Модулей)
├── requirements.txt        # Версии зависимостей Python
├── package.json            # npm конфигурация Convex
├── convex/                 # TypeScript бэкенд Convex DB
│   ├── schema.ts           # Расширенная схема PIM (chats, messages, journals, projects, notes, vault)
│   ├── chats.ts            # Обработчики диалогов
│   ├── messages.ts         # Обработчики сообщений
│   ├── journals.ts         # Обработчики журнала
│   ├── projects.ts         # Обработчики проектов
│   ├── notes.ts            # Обработчики заметок
│   └── vault.ts            # Обработчики зашифрованного сейфа
└── providers/              # Провайдеры API и сервис безопасности
    ├── security.py         # Шифрование AES-256 (Fernet) и Валидация Gemini API Key
    ├── convex_client.py    # Python ConvexBridge для синхронизации
    ├── gemini_client.py    # Клиент Google Gemini
    ├── anthropic_client.py # Клиент Anthropic Claude
    └── mistral_client.py   # Клиент Mistral AI
```

---

## 🔐 Шифрование и Безопасность (Security Service)

Модуль `providers/security.py` отвечает за два уровня защиты:
1. **`verify_gemini_api_key(api_key)`**: Делает официальный вызов `genai.list_models()` к Google API для подтверждения валидности API-ключа при входе.
2. **`encrypt_secret(plain_text, passphrase)` & `decrypt_secret(encrypted_text, passphrase)`**: Выполняет хэширование SHA-256 мастер-пароля для генерации 256-битного Fernet-ключа и зашифровывает данные Сейфа перед отправкой в Convex DB.

---

## 🗄️ База Данных Convex DB

Схема базы зафиксирована в `convex/schema.ts`:
* `chats` — Таблица настроек диалогов
* `messages` — История сообщений
* `journals` — Ежедневный журнал с рефлексией
* `projects` — Проекты, категории и milestones
* `notes` — База знаний и заметки
* `vault` — Зашифрованные записи сейфа

Для применения новой схемы в облаке Convex выполняйте:
```bash
npx convex dev
```

---

## ⚡ Antigravity 2.0 Integration

В проекте активны интеграционные точки для Antigravity 2.0:
* Локальный агент Antigravity в IDE имеет прямой доступ к модулю `providers/convex_client.py` и умеет автоматизировать тестирование и индексацию заметок.
