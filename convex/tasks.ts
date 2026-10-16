import { internalMutation, internalQuery } from "./_generated/server";
import { v } from "convex/values";

export const listTasks = internalQuery({
    args: {},
    returns: v.any(),
    handler: async (ctx) => {
        return await ctx.db.query("tasks").order("desc").take(200);
    },
});

export const save = internalMutation({
    args: {
        id: v.string(),
        title: v.string(),
        description: v.optional(v.string()),
        startDate: v.optional(v.string()),
        endDate: v.optional(v.string()),
        projectId: v.optional(v.string()),
        category: v.string(),
    },
    returns: v.any(),
    handler: async (ctx, args) => {
        const now = Date.now();
        return await ctx.db.insert("tasks", {
            ...args,
            createdAt: now,
            updatedAt: now,
        });
    },
});

export const update = internalMutation({
    args: {
        id: v.string(),
        title: v.optional(v.string()),
        description: v.optional(v.string()),
        startDate: v.optional(v.string()),
        endDate: v.optional(v.string()),
        projectId: v.optional(v.string()),
        category: v.optional(v.string()),
    },
    returns: v.any(),
    handler: async (ctx, args) => {
        const existing = await ctx.db
            .query("tasks")
            .withIndex("by_uuid", (q) => q.eq("id", args.id))
            .first();
        if (!existing) return null;

        const updateData: Record<string, unknown> = { updatedAt: Date.now() };
        if (args.title !== undefined) updateData.title = args.title;
        if (args.description !== undefined) updateData.description = args.description;
        if (args.startDate !== undefined) updateData.startDate = args.startDate;
        if (args.endDate !== undefined) updateData.endDate = args.endDate;
        if (args.projectId !== undefined) updateData.projectId = args.projectId;
        if (args.category !== undefined) updateData.category = args.category;

        await ctx.db.patch(existing._id, updateData);
        return existing._id;
    },
});

export const deleteTask = internalMutation({
    args: { id: v.string() },
    returns: v.boolean(),
    handler: async (ctx, args) => {
        const existing = await ctx.db
            .query("tasks")
            .withIndex("by_uuid", (q) => q.eq("id", args.id))
            .first();
        if (!existing) return false;
        await ctx.db.delete(existing._id);
        return true;
    },
});

export const listByDate = internalQuery({
    args: { date: v.string() },
    returns: v.any(),
    handler: async (ctx, args) => {
        const tasks = await ctx.db.query("tasks").order("desc").take(200);
        return tasks.filter((task) =>
            (!task.startDate || task.startDate <= args.date)
            && (!task.endDate || task.endDate >= args.date)
        );
    },
});
