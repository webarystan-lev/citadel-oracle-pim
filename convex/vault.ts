import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const listVaultEntries = query({
    handler: async (ctx) => {
        return await ctx.db.query("vault").order("desc").take(100);
    },
});

export const createVaultEntry = mutation({
    args: {
        id: v.string(),
        title: v.string(),
        secretType: v.string(),
        encryptedPayload: v.string(),
        serviceName: v.optional(v.string()),
        note: v.optional(v.string()),
    },
    handler: async (ctx, args) => {
        const now = Date.now();
        return await ctx.db.insert("vault", {
            id: args.id,
            title: args.title,
            secretType: args.secretType,
            encryptedPayload: args.encryptedPayload,
            serviceName: args.serviceName,
            note: args.note,
            createdAt: now,
            updatedAt: now,
        });
    },
});

export const updateVaultEntry = mutation({
    args: {
        id: v.string(),
        title: v.optional(v.string()),
        secretType: v.optional(v.string()),
        encryptedPayload: v.optional(v.string()),
        serviceName: v.optional(v.string()),
        note: v.optional(v.string()),
    },
    handler: async (ctx, args) => {
        const existing = await ctx.db
            .query("vault")
            .withIndex("by_uuid", (q) => q.eq("id", args.id))
            .first();

        if (!existing) return null;

        const updateData: any = { updatedAt: Date.now() };
        if (args.title !== undefined) updateData.title = args.title;
        if (args.secretType !== undefined) updateData.secretType = args.secretType;
        if (args.encryptedPayload !== undefined) updateData.encryptedPayload = args.encryptedPayload;
        if (args.serviceName !== undefined) updateData.serviceName = args.serviceName;
        if (args.note !== undefined) updateData.note = args.note;

        await ctx.db.patch(existing._id, updateData);
        return existing._id;
    },
});

export const deleteVaultEntry = mutation({
    args: { id: v.string() },
    handler: async (ctx, args) => {
        const existing = await ctx.db
            .query("vault")
            .withIndex("by_uuid", (q) => q.eq("id", args.id))
            .first();
        if (existing) {
            await ctx.db.delete(existing._id);
            return true;
        }
        return false;
    },
});
