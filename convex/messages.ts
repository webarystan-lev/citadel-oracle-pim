import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

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

export const add = mutation({
    args: {
        chatId: v.string(),
        role: v.string(),
        content: v.string(),
        thinking: v.optional(v.string()),
        meta: v.optional(v.string()),
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

export const clearChat = mutation({
    args: { chatId: v.string() },
    handler: async (ctx, args) => {
        const messages = await ctx.db
            .query("messages")
            .withIndex("by_chatId", (q) => q.eq("chatId", args.chatId))
            .collect();
        for (const msg of messages) {
            await ctx.db.delete(msg._id);
        }
        return true;
    },
});
