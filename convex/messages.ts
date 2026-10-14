import { internalAction, internalMutation, internalQuery } from "./_generated/server";
import { v } from "convex/values";
import { paginationOptsValidator } from "convex/server";
import { internal } from "./_generated/api";

export const listForChat = internalQuery({
    args: {
        chatId: v.string(),
        paginationOpts: v.optional(paginationOptsValidator),
    },
    returns: v.any(),
    handler: async (ctx, args) => {
        return await ctx.db
            .query("messages")
            .withIndex("by_chatId", (q) => q.eq("chatId", args.chatId))
            .order("asc")
            .paginate(args.paginationOpts ?? { numItems: 100, cursor: null });
    },
});

export const add = internalMutation({
    args: {
        chatId: v.string(),
        role: v.string(),
        content: v.string(),
        thinking: v.optional(v.string()),
        meta: v.optional(v.string()),
    },
    returns: v.any(),
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

export const clearChatBatch = internalMutation({
    args: { chatId: v.string() },
    returns: v.boolean(),
    handler: async (ctx, args) => {
        const messages = await ctx.db
            .query("messages")
            .withIndex("by_chatId", (q) => q.eq("chatId", args.chatId))
            .order("asc")
            .take(500);
        for (const msg of messages) {
            await ctx.db.delete(msg._id);
        }
        return messages.length === 500;
    },
});

export const clearChat = internalAction({
    args: { chatId: v.string() },
    returns: v.boolean(),
    handler: async (ctx, args) => {
        let hasMore = true;
        while (hasMore) {
            hasMore = await ctx.runMutation(internal.messages.clearChatBatch, args);
        }
        return true;
    },
});
