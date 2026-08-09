import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// Получение списка всех записей журнала
export const listJournals = query({
    handler: async (ctx) => {
        return await ctx.db.query("journals").order("desc").take(100);
    },
});

// Добавление новой записи в журнал
export const createJournal = mutation({
    args: {
        id: v.string(),
        date: v.string(),
        title: v.string(),
        content: v.string(),
        tags: v.array(v.string()),
        reflectionQuestions: v.optional(v.string()),
        aiSynthesis: v.optional(v.string()),
    },
    handler: async (ctx, args) => {
        const now = Date.now();
        return await ctx.db.insert("journals", {
            id: args.id,
            date: args.date,
            title: args.title,
            content: args.content,
            tags: args.tags,
            reflectionQuestions: args.reflectionQuestions,
            aiSynthesis: args.aiSynthesis,
            createdAt: now,
            updatedAt: now,
        });
    },
});

// Обновление записи в журнале
export const updateJournal = mutation({
    args: {
        id: v.string(),
        title: v.optional(v.string()),
        content: v.optional(v.string()),
        tags: v.optional(v.array(v.string())),
        reflectionQuestions: v.optional(v.string()),
        aiSynthesis: v.optional(v.string()),
    },
    handler: async (ctx, args) => {
        const existing = await ctx.db
            .query("journals")
            .withIndex("by_uuid", (q) => q.eq("id", args.id))
            .first();

        if (!existing) return null;

        const updateData: any = { updatedAt: Date.now() };
        if (args.title !== undefined) updateData.title = args.title;
        if (args.content !== undefined) updateData.content = args.content;
        if (args.tags !== undefined) updateData.tags = args.tags;
        if (args.reflectionQuestions !== undefined) updateData.reflectionQuestions = args.reflectionQuestions;
        if (args.aiSynthesis !== undefined) updateData.aiSynthesis = args.aiSynthesis;

        await ctx.db.patch(existing._id, updateData);
        return existing._id;
    },
});

// Удаление записи журнала
export const deleteJournal = mutation({
    args: { id: v.string() },
    handler: async (ctx, args) => {
        const existing = await ctx.db
            .query("journals")
            .withIndex("by_uuid", (q) => q.eq("id", args.id))
            .first();
        if (existing) {
            await ctx.db.delete(existing._id);
            return true;
        }
        return false;
    },
});
