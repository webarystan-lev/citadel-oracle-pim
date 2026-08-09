# 🏛️ Свиток Настройки Бэкенда Convex DB

Этот манускрипт содержит полную схему данных и исходный код TypeScript функций, необходимых для запуска и обслуживания облачной базы данных **Convex DB** для проекта **Shekinah AI Portal**.

---

## 📁 1. Структура Папки Convex

В корневом каталоге Вашего проекта Convex (или в папке `convex/` Вашего Fullstack-приложения) должна быть следующая структура:

```
convex/
├── _generated/         # Автоматически генерируемые файлы (создаются Convex CLI)
├── schema.ts           # Священная схема таблиц (Спецификация типов)
├── chats.ts            # Мутации и запросы для управления диалогами
└── messages.ts         # Мутации и запросы для сохранения реплик и мыслей
```

---

## 📜 2. Священная Схема — `convex/schema.ts`

Скопируйте этот код в файл `schema.ts`. Он описывает таблицы `chats` (диалоги) и `messages` (сообщения) с необходимыми индексами для сверхбыстрого поиска.

```typescript
import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  // Таблица диалогов
  chats: defineTable({
    id: v.string(),             // UUID диалога из Streamlit сессии
    title: v.string(),          // Заголовок диалога
    provider: v.string(),       // Выбранный провайдер (например, "Google Gemini")
    model: v.string(),          // Название модели (например, "gemini-2.5-flash")
    systemPrompt: v.string(),   // Инструкция для ИИ
    temperature: v.float64(),   // Креативность генерации
    maxTokens: v.float64(),     // Максимальный лимит токенов
    createdAt: v.float64(),     // Временной штамп создания (timestamp)
  }).index("by_id", ["id"]),

  // Таблица сообщений
  messages: defineTable({
    chatId: v.string(),         // Внешний ключ: UUID диалога
    role: v.string(),           // Роль автора реплики ("user" / "assistant")
    content: v.string(),        // Текст сообщения
    thinking: v.optional(v.string()), // Скрытый блок размышлений модели (thinking)
    meta: v.optional(v.string()),     // JSON-сериализованный словарь метаданных (время, чин и др.)
    createdAt: v.float64(),     // Временной штамп добавления
  }).index("by_chatId", ["chatId"]),
});
```

---

## 🛠️ 3. Серверные Функции Диалогов — `convex/chats.ts`

Скопируйте этот код в файл `chats.ts`. Он обеспечивает извлечение, сохранение, переименование и бесследное удаление чатов.

```typescript
import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

// 📖 Получить список всех чатов, упорядоченных от новых к старым
export const list = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("chats").order("desc").collect();
  },
});

// ✍️ Сохранить или обновить параметры диалога
export const save = mutation({
  args: {
    id: v.string(),
    title: v.string(),
    provider: v.string(),
    model: v.string(),
    systemPrompt: v.string(),
    temperature: v.float64(),
    maxTokens: v.float64(),
  },
  handler: async (ctx, args) => {
    // Ищем существующий чат с данным UUID
    const existing = await ctx.db
      .query("chats")
      .withIndex("by_id", (q) => q.eq("id", args.id))
      .unique();

    if (existing) {
      // Обновляем параметры чата
      await ctx.db.patch(existing._id, {
        title: args.title,
        provider: args.provider,
        model: args.model,
        systemPrompt: args.systemPrompt,
        temperature: args.temperature,
        maxTokens: args.maxTokens,
      });
      return existing._id;
    } else {
      // Создаем новую запись
      return await ctx.db.insert("chats", {
        id: args.id,
        title: args.title,
        provider: args.provider,
        model: args.model,
        systemPrompt: args.systemPrompt,
        temperature: args.temperature,
        maxTokens: args.maxTokens,
        createdAt: Date.now(),
      });
    }
  },
});

// ✏️ Изменить заголовок диалога
export const rename = mutation({
  args: {
    id: v.string(),
    title: v.string(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("chats")
      .withIndex("by_id", (q) => q.eq("id", args.id))
      .unique();

    if (existing) {
      await ctx.db.patch(existing._id, { title: args.title });
    }
  },
});

// 🗑️ Полное удаление диалога и всех его реплик
export const remove = mutation({
  args: {
    id: v.string(),
  },
  handler: async (ctx, args) => {
    // 1. Находим и удаляем запись диалога
    const existing = await ctx.db
      .query("chats")
      .withIndex("by_id", (q) => q.eq("id", args.id))
      .unique();

    if (existing) {
      await ctx.db.delete(existing._id);
    }

    // 2. Находим и очищаем все сообщения, привязанные к этому диалогу
    const msgs = await ctx.db
      .query("messages")
      .withIndex("by_chatId", (q) => q.eq("chatId", args.id))
      .collect();

    for (const msg of msgs) {
      await ctx.db.delete(msg._id);
    }
  },
});
```

---

## 💬 4. Серверные Функции Сообщений — `convex/messages.ts`

Скопируйте этот код в файл `messages.ts`. Он отвечает за чтение реплик, запись новых высказываний и сброс истории в чате.

```typescript
import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

// 📖 Загрузить хронологическую историю сообщений для конкретного диалога
export const listForChat = query({
  args: { chatId: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("messages")
      .withIndex("by_chatId", (q) => q.eq("chatId", args.chatId))
      .order("asc")
      .collect();
  },
});

// ✍️ Добавить новое сообщение (реплику) в диалог
export const add = mutation({
  args: {
    chatId: v.string(),
    role: v.string(),
    content: v.string(),
    thinking: v.optional(v.string()),
    meta: v.optional(v.string()), // Сериализованная строка JSON
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("messages", {
      chatId: args.chatId,
      role: args.role,
      content: args.content,
      thinking: args.thinking,
      meta: args.meta,
      createdAt: Date.now(),
    });
  },
});

// 🧹 Очистить историю сообщений конкретного диалога
export const clearChat = mutation({
  args: { chatId: v.string() },
  handler: async (ctx, args) => {
    const msgs = await ctx.db
      .query("messages")
      .withIndex("by_chatId", (q) => q.eq("chatId", args.chatId))
      .collect();

    for (const msg of msgs) {
      await ctx.db.delete(msg._id);
    }
  },
});
```

---

## 🚀 5. Как развернуть бэкенд

1. Установите Convex CLI в Вашем бэкенд-проекте, если это новый проект:
   ```bash
   npm install convex
   ```
2. Инициализируйте проект Convex и свяжите его с Вашим личным облачным кабинетом:
   ```bash
   npx convex dev
   ```
   *Команда предложит авторизоваться и автоматически создаст для Вас уникальный URL вида `https://elegant-gundog-123.convex.cloud`. Это значение нужно прописать в Ваш файл `.env` как `CONVEX_URL`.*

3. Разместите созданные файлы в папку `convex/` и они автоматически синхронизируются с облаком!
```,Description:
