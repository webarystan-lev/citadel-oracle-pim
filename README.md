# 🏛️ Citadel Oracle PIM (Personal Information Manager & Knowledge Hub)
> *«Се, Я полагаю в Сионе камень краеугольный, избранный, драгоценный...» (1 Петра 2:6)*

**Citadel Oracle PIM** — это суверенный цифровой органайзер, база знаний, зашифрованный сейф паролей и персональный ИИ-Оракул, созданный для **Льва Николаевича** (пастора с 2002 года, миссионера, руководителя «Миссии Шехина» и основателя **Web Development Studio Web Arystan**).

Система спроектирована специально для размещения в интернете с возможностью защищенного доступа из любых миссионерских поездок и локаций, обеспечивая безопасную работу с информацией, проектами и молитвенными журналами.

🌐 **Официальный Публичный Веб-Адрес**: [https://citadel-oracle.streamlit.app](https://citadel-oracle.streamlit.app)

---

## 🌟 Ключевые Модули Системы

1. **💬 ИИ-Чат & Персональный Оракул**:
   * Мультипровайдерные диалоги в реальном времени с поддержкой живого динамического запроса доступных моделей:
     * **Google Gemini**: `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.5-flash-lite`, `gemini-3.5-flash`, `gemini-3.6-flash`, `gemma-4-31b-it` и др.
     * **Anthropic Claude**: `claude-opus-5`, `claude-sonnet-5`, `claude-sonnet-4-6`, `claude-haiku-4-5` и др.
     * **Mistral AI**: `mistral-large-latest`, `codestral-latest`, `devstral-latest`, `mistral-medium-latest` и др.
   * Управление параметрами генерации (Temperature, Max Tokens, System Prompt).
   * Обязательная подпись Ордена (**Shekinah Citadel Oracle Spirit**) к каждому ответу.
   * Экспорт диалогов в структурированный Markdown.

2. **📖 Ежедневный Журнал (Journal with Gemini)**:
   * Запись повседневных мыслей, рефлексии и духовных благословений.
   * Автоматическая генерация ИИ-вопросов для вечерней размышления в 1 клик.
   * Синтез и тегирование дневниковых записей.

3. **📁 Управление Проектами (Project Hub)**:
   * Отслеживание проектов (*Миссия Шехина*, *Web Arystan*, *Citadel Cloud*, *AI Oracle PIM*).
   * Статусы (`Active`, `Planning`, `Completed`, `Archived`), категории и этапные цели (Milestones).

4. **📝 Заметки & База Знаний**:
   * Конспекты Писания, теологические заметки, статьи и техническая документация.

5. **🔐 Зашифрованный Сейф Паролей и Ключей**:
   * Безопасное хранение API-ключей, токенов и паролей с шифрованием по стандарту **AES-256 (Fernet)**.

---

## 🛠️ Требования к Окружению

Перед началом установки убедитесь, что в Вашей системе установлены:
* **Python**: версия `3.11` или выше
* **Node.js**: версия `18.x` или `20.x` (для управления Convex DB)
* **npm**: поставляется вместе с Node.js
* **Git**: для клонирования и управления версиями

---

## 🚀 Пошаговое Руководство по Клонированию и Локальному Развертыванию

### Шаг 1. Клонирование Репозитория
Откройте терминал и выполните команду клонирования:

```bash
git clone https://github.com/webarystan-lev/citadel-oracle-pim.git
cd citadel-oracle-pim
```

---

### Шаг 2. Настройка Python Окружения и Зависимостей

1. **Создайте и активируйте виртуальное окружение**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Установите требуемые Python-пакеты**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

   *Содержимое `requirements.txt`:*
   * `streamlit==1.58.0`
   * `google-genai`
   * `anthropic==0.116.0`
   * `mistralai==2.5.2`
   * `cryptography==42.0.8`
   * `convex==0.7.0`
   * `python-dotenv==1.2.2`

---

### Шаг 3. Инициализация и Настройка Облачной Бэкенд-БД Convex DB

Система использует **Convex DB** для синхронизации всех данных (чаты, журналы, проекты, заметки, сейф).

1. **Установите Node-зависимости**:
   ```bash
   npm install
   ```

2. **Войдите и инициализируйте Convex**:
   ```bash
   npx convex dev
   ```
   * Команда предложит войти через браузер в аккаунт Convex.
   * Будет создан проект в вашем аккаунте Convex и сформирован файл `.env.local` с переменными `CONVEX_URL` и `CONVEX_DEPLOYMENT`.
   * Автоматически развернется схема из директории `convex/` (`schema.ts`, `chats.ts`, `journals.ts`, `projects.ts`, `notes.ts`, `vault.ts`).

3. **Развертывание схемы в Production (при необходимости)**:
   ```bash
   npx convex deploy
   ```

---

### Шаг 4. Настройка Переменных Окружения (`.env`)

Создайте файл `.env` в корневом каталоге проекта со следующим содержимым:

```env
# 🛡️ Мастер-пароль для входа в Citadel PIM
PIM_SECRET_KEY=ваш_надежный_секретный_пароль

# 🔑 API-ключ Google Gemini (обязателен для входа и проверки подлинности)
GEMINI_API_KEY=AIzaSy...ваш_ключ_gemini

# 🔑 Необязательные ключи альтернативных провайдеров
ANTHROPIC_API_KEY=sk-ant-...ваш_ключ_anthropic
MISTRAL_API_KEY=...ваш_ключ_mistral

# 🌐 URL Вашей бэкенд-базы данных Convex DB (скопируйте из .env.local или панели Convex)
CONVEX_URL=https://ваша-бд.convex.cloud
```

---

### Шаг 5. Запуск Локального Приложения Streamlit

После успешной настройки `.env` и развертывания Convex DB запустите Streamlit:

```bash
streamlit run app.py
```

После запуска в терминале появится адрес локального сервера:
```text
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

---

### Шаг 6. Авторизация на Экране Gatekeeper

1. Откройте `http://localhost:8501` в браузере.
2. Введите Ваш `PIM_SECRET_KEY` и `GEMINI_API_KEY`.
3. Система выполнит живой вызов к API Google Gemini для валидации ключа.
4. При успешной проверке доступ к обители будет открыт!

---

## 📂 Архитектура и Структура Файлов

```
citadel-oracle-pim/
├── .env                    # Секретные ключи PIM_SECRET_KEY, GEMINI_API_KEY, CONVEX_URL
├── app.py                  # Главный интерфейс PIM (Streamlit + Авторизация + 5 Модулей)
├── requirements.txt        # Зависимости Python
├── package.json            # Node.js манифест Convex DB
├── GEMINI.md               # Свиток Состояния Проекта (Project State Ledger)
├── AGENTS.md               # Реестр ИИ-Агентов Цитадели
├── README.md               # Документация и Руководство по Развертыванию
├── convex/                 # TypeScript Бэкенд Convex DB
│   ├── schema.ts           # Схема БД (chats, messages, journals, projects, notes, vault)
│   ├── chats.ts            # Обработчики чатов
│   ├── journals.ts         # Обработчики дневника
│   ├── projects.ts         # Обработчики проектов
│   ├── notes.ts            # Обработчики заметок
│   └── vault.ts            # Обработчики шифрованного сейфа
└── providers/              # Провайдеры ИИ и Служба Безопасности
    ├── security.py         # Шифрование AES-256 Fernet & Валидация Gemini API Key
    ├── convex_client.py    # Python ConvexBridge
    ├── gemini_client.py    # Динамический клиент Google Gemini
    ├── anthropic_client.py # Динамический клиент Anthropic Claude
    └── mistral_client.py   # Динамический клиент Mistral AI
```

---

## 🛡️ Правила Внесения Изменений и Деплоя

Согласно Уставу Цитадели ([AGENTS.md](file:///home/lev/AI-Projects/Hub-webarystan@gmail.com/citadel-oracle-pim/AGENTS.md)), деплой и публикация изменений осуществляются строго по прямой команде **Льва Николаевича**:

```bash
git add .
git commit -m "описание изменений"
git push origin main
```

*«Устрой пути свои пред Господом, и помыслы твои совершатся» (Притчи 16:3).*
