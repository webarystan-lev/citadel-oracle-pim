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
