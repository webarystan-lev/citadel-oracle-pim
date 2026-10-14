import { httpRouter } from "convex/server";
import type { FunctionArgs, FunctionReference } from "convex/server";
import { httpAction } from "./_generated/server";
import { internal } from "./_generated/api";

const http = httpRouter();

function constantTimeEqual(left: string, right: string): boolean {
    let difference = left.length ^ right.length;
    const length = Math.max(left.length, right.length);
    for (let index = 0; index < length; index += 1) {
        difference |= (left.charCodeAt(index) || 0) ^ (right.charCodeAt(index) || 0);
    }
    return difference === 0;
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

function gatewayArgs<
    Reference extends FunctionReference<"query" | "mutation" | "action", "internal">
>(
    args: Record<string, unknown>,
): FunctionArgs<Reference> {
    // Convex validates these untrusted JSON arguments against the referenced function's args validator.
    return args as FunctionArgs<Reference>;
}

const pimApi = httpAction(async (ctx, request) => {
    const configuredSecret = process.env.CONVEX_API_SECRET;
    const authorization = request.headers.get("Authorization") ?? "";
    const suppliedSecret = authorization.startsWith("Bearer ")
        ? authorization.slice("Bearer ".length)
        : "";

    if (!configuredSecret || suppliedSecret.length > 512 || !constantTimeEqual(suppliedSecret, configuredSecret)) {
        return Response.json({ error: "Unauthorized" }, { status: 401 });
    }

    let body: unknown;
    try {
        body = await request.json();
    } catch {
        return Response.json({ error: "Invalid JSON request" }, { status: 400 });
    }

    if (!isRecord(body) || typeof body.operation !== "string") {
        return Response.json({ error: "An operation is required" }, { status: 400 });
    }

    const args = body.args ?? {};
    if (!isRecord(args)) {
        return Response.json({ error: "Operation arguments must be an object" }, { status: 400 });
    }

    try {
        let result: unknown;
        switch (body.operation) {
            case "chats:list":
                result = await ctx.runQuery(internal.chats.list, {});
                break;
            case "chats:save":
                result = await ctx.runMutation(internal.chats.save, gatewayArgs<typeof internal.chats.save>(args));
                break;
            case "chats:rename":
                result = await ctx.runMutation(internal.chats.rename, gatewayArgs<typeof internal.chats.rename>(args));
                break;
            case "chats:remove":
                result = await ctx.runAction(internal.chats.remove, gatewayArgs<typeof internal.chats.remove>(args));
                break;
            case "messages:listForChat":
                result = await ctx.runQuery(internal.messages.listForChat, gatewayArgs<typeof internal.messages.listForChat>(args));
                break;
            case "messages:add":
                result = await ctx.runMutation(internal.messages.add, gatewayArgs<typeof internal.messages.add>(args));
                break;
            case "notebooks:listNotebooks":
                result = await ctx.runQuery(internal.notebooks.listNotebooks, {});
                break;
            case "notebooks:createNotebook":
                result = await ctx.runMutation(internal.notebooks.createNotebook, gatewayArgs<typeof internal.notebooks.createNotebook>(args));
                break;
            case "notebooks:deleteNotebook":
                result = await ctx.runMutation(internal.notebooks.deleteNotebook, gatewayArgs<typeof internal.notebooks.deleteNotebook>(args));
                break;
            case "journals:listJournals":
                result = await ctx.runQuery(internal.journals.listJournals, {});
                break;
            case "journals:listJournalsByNotebook":
                result = await ctx.runQuery(internal.journals.listJournalsByNotebook, gatewayArgs<typeof internal.journals.listJournalsByNotebook>(args));
                break;
            case "journals:createJournal":
                result = await ctx.runMutation(internal.journals.createJournal, gatewayArgs<typeof internal.journals.createJournal>(args));
                break;
            case "journals:updateJournal":
                result = await ctx.runMutation(internal.journals.updateJournal, gatewayArgs<typeof internal.journals.updateJournal>(args));
                break;
            case "journals:deleteJournal":
                result = await ctx.runMutation(internal.journals.deleteJournal, gatewayArgs<typeof internal.journals.deleteJournal>(args));
                break;
            case "projects:listProjects":
                result = await ctx.runQuery(internal.projects.listProjects, {});
                break;
            case "projects:createProject":
                result = await ctx.runMutation(internal.projects.createProject, gatewayArgs<typeof internal.projects.createProject>(args));
                break;
            case "projects:deleteProject":
                result = await ctx.runMutation(internal.projects.deleteProject, gatewayArgs<typeof internal.projects.deleteProject>(args));
                break;
            case "notes:listNotes":
                result = await ctx.runQuery(internal.notes.listNotes, {});
                break;
            case "notes:createNote":
                result = await ctx.runMutation(internal.notes.createNote, gatewayArgs<typeof internal.notes.createNote>(args));
                break;
            case "notes:deleteNote":
                result = await ctx.runMutation(internal.notes.deleteNote, gatewayArgs<typeof internal.notes.deleteNote>(args));
                break;
            case "vault:listVaultEntries":
                result = await ctx.runQuery(internal.vault.listVaultEntries, {});
                break;
            case "vault:createVaultEntry":
                result = await ctx.runMutation(internal.vault.createVaultEntry, gatewayArgs<typeof internal.vault.createVaultEntry>(args));
                break;
            case "vault:deleteVaultEntry":
                result = await ctx.runMutation(internal.vault.deleteVaultEntry, gatewayArgs<typeof internal.vault.deleteVaultEntry>(args));
                break;
            default:
                return Response.json({ error: "Unknown operation" }, { status: 404 });
        }
        return Response.json({ result });
    } catch {
        return Response.json({ error: "The requested operation failed" }, { status: 500 });
    }
});

http.route({
    path: "/pim",
    method: "POST",
    handler: pimApi,
});

export default http;
