import { internalAction, internalMutation, internalQuery } from "./_generated/server";
import { v } from "convex/values";
import { internal } from "./_generated/api";

export const list = internalQuery({
    args: {},
    returns: v.any(),
    handler: async (ctx) => {
        return await ctx.db.query("chats").order("desc").take(100);
    },
});

export const save = internalMutation({
    args: {
        id: v.string(),
        title: v.string(),
        provider: v.string(),
        model: v.string(),
        systemPrompt: v.string(),
        temperature: v.float64(),
        maxTokens: v.float64(),
    },
    returns: v.any(),
    handler: async (ctx, args) => {
        const existing = await ctx.db
            .query("chats")
            .withIndex("by_uuid", (q) => q.eq("id", args.id))
            .first();

        const now = Date.now();
        if (existing) {
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
            return await ctx.db.insert("chats", {
                id: args.id,
                title: args.title,
                provider: args.provider,
                model: args.model,
                systemPrompt: args.systemPrompt,
                temperature: args.temperature,
                maxTokens: args.maxTokens,
                createdAt: now,
            });
        }
    },
});

export const rename = internalMutation({
    args: {
        id: v.string(),
        title: v.string(),
    },
    returns: v.any(),
    handler: async (ctx, args) => {
        const existing = await ctx.db
            .query("chats")
            .withIndex("by_uuid", (q) => q.eq("id", args.id))
            .first();

        if (existing) {
            await ctx.db.patch(existing._id, { title: args.title });
            return true;
        }
        return false;
    },
});

export const removeBatch = internalMutation({
    args: { id: v.string() },
    returns: v.any(),
    handler: async (ctx, args) => {
        const existing = await ctx.db
            .query("chats")
            .withIndex("by_uuid", (q) => q.eq("id", args.id))
            .first();

        const messages = await ctx.db
            .query("messages")
            .withIndex("by_chatId", (q) => q.eq("chatId", args.id))
            .order("asc")
            .take(500);
        for (const msg of messages) {
            await ctx.db.delete(msg._id);
        }
        if (messages.length < 500) {
            if (existing) {
                await ctx.db.delete(existing._id);
            }
            return false;
        }
        return true;
    },
});

export const remove = internalAction({
    args: { id: v.string() },
    returns: v.boolean(),
    handler: async (ctx, args) => {
        let hasMore = true;
        while (hasMore) {
            hasMore = await ctx.runMutation(internal.chats.removeBatch, args);
        }
        return true;
    },
});
