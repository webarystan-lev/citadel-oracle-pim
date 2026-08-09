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
        .withIndex("by_uuid", (q) => q.eq("id", args.id))
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
        .withIndex("by_uuid", (q) => q.eq("id", args.id))
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
        .withIndex("by_uuid", (q) => q.eq("id", args.id))
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
