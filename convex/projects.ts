import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const listProjects = query({
    handler: async (ctx) => {
        return await ctx.db.query("projects").order("desc").take(100);
    },
});

export const createProject = mutation({
    args: {
        id: v.string(),
        title: v.string(),
        description: v.string(),
        status: v.string(),
        category: v.string(),
        milestones: v.optional(v.string()),
        tags: v.array(v.string()),
    },
    handler: async (ctx, args) => {
        const now = Date.now();
        return await ctx.db.insert("projects", {
            id: args.id,
            title: args.title,
            description: args.description,
            status: args.status,
            category: args.category,
            milestones: args.milestones,
            tags: args.tags,
            createdAt: now,
            updatedAt: now,
        });
    },
});

export const updateProject = mutation({
    args: {
        id: v.string(),
        title: v.optional(v.string()),
        description: v.optional(v.string()),
        status: v.optional(v.string()),
        category: v.optional(v.string()),
        milestones: v.optional(v.string()),
        tags: v.optional(v.array(v.string())),
    },
    handler: async (ctx, args) => {
        const existing = await ctx.db
            .query("projects")
            .withIndex("by_uuid", (q) => q.eq("id", args.id))
            .first();

        if (!existing) return null;

        const updateData: any = { updatedAt: Date.now() };
        if (args.title !== undefined) updateData.title = args.title;
        if (args.description !== undefined) updateData.description = args.description;
        if (args.status !== undefined) updateData.status = args.status;
        if (args.category !== undefined) updateData.category = args.category;
        if (args.milestones !== undefined) updateData.milestones = args.milestones;
        if (args.tags !== undefined) updateData.tags = args.tags;

        await ctx.db.patch(existing._id, updateData);
        return existing._id;
    },
});

export const deleteProject = mutation({
    args: { id: v.string() },
    handler: async (ctx, args) => {
        const existing = await ctx.db
            .query("projects")
            .withIndex("by_uuid", (q) => q.eq("id", args.id))
            .first();
        if (existing) {
            await ctx.db.delete(existing._id);
            return true;
        }
        return false;
    },
});
