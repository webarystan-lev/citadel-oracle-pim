import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const list = query({
    handler: async (ctx) => {
        return await ctx.db.query("chats").order("desc").take(100);
    },
});

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

export const rename = mutation({
    args: {
        id: v.string(),
        title: v.string(),
    },
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

export const remove = mutation({
    args: { id: v.string() },
    handler: async (ctx, args) => {
        const existing = await ctx.db
            .query("chats")
            .withIndex("by_uuid", (q) => q.eq("id", args.id))
            .first();

        if (existing) {
            const messages = await ctx.db
                .query("messages")
                .withIndex("by_chatId", (q) => q.eq("chatId", args.id))
                .collect();
            for (const msg of messages) {
                await ctx.db.delete(msg._id);
            }
            await ctx.db.delete(existing._id);
            return true;
        }
        return false;
    },
});
