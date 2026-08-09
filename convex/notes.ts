import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const listNotes = query({
    handler: async (ctx) => {
        return await ctx.db.query("notes").order("desc").take(200);
    },
});

export const createNote = mutation({
    args: {
        id: v.string(),
        title: v.string(),
        category: v.string(),
        content: v.string(),
        tags: v.array(v.string()),
        isArchived: v.boolean(),
    },
    handler: async (ctx, args) => {
        const now = Date.now();
        return await ctx.db.insert("notes", {
            id: args.id,
            title: args.title,
            category: args.category,
            content: args.content,
            tags: args.tags,
            isArchived: args.isArchived,
            createdAt: now,
            updatedAt: now,
        });
    },
});

export const updateNote = mutation({
    args: {
        id: v.string(),
        title: v.optional(v.string()),
        category: v.optional(v.string()),
        content: v.optional(v.string()),
        tags: v.optional(v.array(v.string())),
        isArchived: v.optional(v.boolean()),
    },
    handler: async (ctx, args) => {
        const existing = await ctx.db
            .query("notes")
            .withIndex("by_uuid", (q) => q.eq("id", args.id))
            .first();

        if (!existing) return null;

        const updateData: any = { updatedAt: Date.now() };
        if (args.title !== undefined) updateData.title = args.title;
        if (args.category !== undefined) updateData.category = args.category;
        if (args.content !== undefined) updateData.content = args.content;
        if (args.tags !== undefined) updateData.tags = args.tags;
        if (args.isArchived !== undefined) updateData.isArchived = args.isArchived;

        await ctx.db.patch(existing._id, updateData);
        return existing._id;
    },
});

export const deleteNote = mutation({
    args: { id: v.string() },
    handler: async (ctx, args) => {
        const existing = await ctx.db
            .query("notes")
            .withIndex("by_uuid", (q) => q.eq("id", args.id))
            .first();
        if (existing) {
            await ctx.db.delete(existing._id);
            return true;
        }
        return false;
    },
});
