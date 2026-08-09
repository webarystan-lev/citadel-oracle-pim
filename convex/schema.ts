import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
    // 💬 Таблица диалогов ИИ
    chats: defineTable({
        id: v.string(),             // UUID диалога
        title: v.string(),          // Заголовок диалога
        provider: v.string(),       // Провайдер ("Google Gemini", "Anthropic Claude", "Mistral AI")
        model: v.string(),          // Модель
        systemPrompt: v.string(),   // Системный промпт
        temperature: v.float64(),   // Температура
        maxTokens: v.float64(),     // Лимит токенов
        createdAt: v.float64(),     // Timestamp создания
    }).index("by_uuid", ["id"]),

    // 💬 Таблица сообщений диалогов
    messages: defineTable({
        chatId: v.string(),         // UUID диалога
        role: v.string(),           // "user" / "assistant"
        content: v.string(),        // Текст сообщения
        thinking: v.optional(v.string()), // Скрытые размышления модели
        meta: v.optional(v.string()),     // JSON метаданных
        createdAt: v.float64(),     // Timestamp создания
    }).index("by_chatId", ["chatId"]),

    // 📖 Таблица «Журнал» (Journal with Gemini style)
    journals: defineTable({
        id: v.string(),                  // UUID записи
        date: v.string(),                // Дата формата YYYY-MM-DD
        title: v.string(),               // Заголовок записи
        content: v.string(),             // Текст дневниковой записи / рефлексии
        tags: v.array(v.string()),       // Теги записи (напр., ["благодать", "миссия"])
        reflectionQuestions: v.optional(v.string()), // Вопросы для вечерней/утренней рефлексии от ИИ
        aiSynthesis: v.optional(v.string()),         // ИИ-выводы и саммари
        createdAt: v.float64(),
        updatedAt: v.float64(),
    }).index("by_uuid", ["id"]).index("by_date", ["date"]),

    // 📁 Таблица «Проекты»
    projects: defineTable({
        id: v.string(),                  // UUID проекта
        title: v.string(),               // Название проекта
        description: v.string(),         // Описание и цели
        status: v.string(),              // "Active", "Planning", "Completed", "Archived"
        category: v.string(),            // "Ministry", "Web Development", "AI System", "Personal"
        milestones: v.optional(v.string()), // JSON или Markdown этапные цели
        tags: v.array(v.string()),
        createdAt: v.float64(),
        updatedAt: v.float64(),
    }).index("by_uuid", ["id"]).index("by_status", ["status"]),

    // 📝 Таблица «Заметки и База Знаний»
    notes: defineTable({
        id: v.string(),                  // UUID заметки
        title: v.string(),               // Название заметки
        category: v.string(),            // "Theology", "Ministry", "Code", "Ideas", "General"
        content: v.string(),             // Содержимое Markdown
        tags: v.array(v.string()),
        isArchived: v.boolean(),
        createdAt: v.float64(),
        updatedAt: v.float64(),
    }).index("by_uuid", ["id"]).index("by_category", ["category"]),

    // 🔐 Таблица «Зашифрованный Сейф Паролей и Ключей»
    vault: defineTable({
        id: v.string(),                  // UUID записи
        title: v.string(),               // Название ключа/сервиса (напр., "Gemini Prod API Key")
        secretType: v.string(),          // "API_KEY", "TOKEN", "SSH_KEY", "PASSWORD", "OTHER"
        encryptedPayload: v.string(),    // Зашифрованные данные (AES-256 base64)
        serviceName: v.optional(v.string()), // Имя сервиса/хоста (напр., "Google AI Studio")
        note: v.optional(v.string()),    // Публичное примечание (не содержит секрет)
        createdAt: v.float64(),
        updatedAt: v.float64(),
    }).index("by_uuid", ["id"]).index("by_secretType", ["secretType"]),
});
