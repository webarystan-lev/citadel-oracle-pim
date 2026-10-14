import { internalMutation, internalQuery } from "./_generated/server";
import { v } from "convex/values";

// Стандартные канонические журналы
const DEFAULT_NOTEBOOKS = [
    {
        id: "nb-ai-webdev",
        title: "AI & WebDev",
        description: "Разработка, архитектура кода, ИИ-агенты, веб-технологии и алгоритмы",
        icon: "🤖",
        categoryType: "AI_WEBDEV"
    },
    {
        id: "nb-mission",
        title: "Миссия Шехина",
        description: "Миссионерские поездки, молитвенные нужды, служение и духовные плоды",
        icon: "🕊️",
        categoryType: "MISSION"
    },
    {
        id: "nb-school-of-christ",
        title: "Школа Христа",
        description: "Ученичество, трансформация сердца, смирение и учение Писания",
        icon: "✝️",
        categoryType: "SCHOOL_OF_CHRIST"
    },
    {
        id: "nb-family",
        title: "Семья & Личное",
        description: "Семейная жизнь, благодарности, мир в доме и личные радости",
        icon: "👨‍👩‍👧‍👦",
        categoryType: "FAMILY"
    },
    {
        id: "nb-theology",
        title: "Теология & Исследования",
        description: "Апологетика, глубокие библейские заметки и доктринальные выводы",
        icon: "📜",
        categoryType: "THEOLOGY"
    },
    {
        id: "nb-favorites",
        title: "Избранное & Вдохновение",
        description: "Особые памятные моменты, драгоценности веры и духовные озарения",
        icon: "⭐",
        categoryType: "GENERAL"
    }
];

export const listNotebooks = internalQuery({
    args: {},
    returns: v.any(),
    handler: async (ctx) => {
        const notebooks = await ctx.db.query("notebooks").order("desc").take(100);
        if (notebooks.length === 0) {
            // Если таблица пуста, возвращаем дефолтные структуры
            const now = Date.now();
            return DEFAULT_NOTEBOOKS.map((nb) => ({
                ...nb,
                createdAt: now,
                updatedAt: now
            }));
        }
        return notebooks;
    },
});

export const seedDefaultNotebooks = internalMutation({
    args: {},
    returns: v.any(),
    handler: async (ctx) => {
        const existing = await ctx.db.query("notebooks").withIndex("by_uuid").first();
        if (!existing) {
            const now = Date.now();
            for (const nb of DEFAULT_NOTEBOOKS) {
                await ctx.db.insert("notebooks", {
                    id: nb.id,
                    title: nb.title,
                    description: nb.description,
                    icon: nb.icon,
                    categoryType: nb.categoryType,
                    createdAt: now,
                    updatedAt: now,
                });
            }
            return true;
        }
        return false;
    },
});

export const createNotebook = internalMutation({
    args: {
        id: v.string(),
        title: v.string(),
        description: v.string(),
        icon: v.string(),
        categoryType: v.string(),
    },
    returns: v.any(),
    handler: async (ctx, args) => {
        const now = Date.now();
        return await ctx.db.insert("notebooks", {
            id: args.id,
            title: args.title,
            description: args.description,
            icon: args.icon,
            categoryType: args.categoryType,
            createdAt: now,
            updatedAt: now,
        });
    },
});

export const deleteNotebook = internalMutation({
    args: { id: v.string() },
    returns: v.any(),
    handler: async (ctx, args) => {
        const existing = await ctx.db
            .query("notebooks")
            .withIndex("by_uuid", (q) => q.eq("id", args.id))
            .first();
        if (existing) {
            await ctx.db.delete(existing._id);
            return true;
        }
        return false;
    },
});
