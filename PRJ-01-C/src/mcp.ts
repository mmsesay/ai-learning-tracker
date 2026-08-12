/**
 * Remote DevAssist MCP client (Streamable HTTP).
 *
 * Connects the harness to Render-hosted tools over HTTPS — no local MCP server.
 * Discovers list_projects / search_code / git_summary and exposes them as AI SDK tools.
 */

import { Agent, setGlobalDispatcher } from "undici";
import { createMCPClient, type MCPClient } from "@ai-sdk/mcp";
import { tool, type Tool } from "ai";
import { z } from "zod";

import type { HarnessConfig } from "./config.js";

// Render free-tier cold starts often exceed undici's default 10s connect timeout.
// Prefer IPv4 — some networks stall on IPv6 routes to Render.
setGlobalDispatcher(new Agent({ connect: { timeout: 90_000, family: 4 } }));

/** Flatten MCP CallToolResult (or plain string) into model-readable text. */
export function textFromMcp(output: unknown): string {
  if (typeof output === "string") return output;
  if (output && typeof output === "object") {
    const content = (
      output as { content?: Array<{ type?: string; text?: string }> }
    ).content;
    if (Array.isArray(content)) {
      const text = content
        .filter((c) => c?.type === "text" && c.text)
        .map((c) => c.text)
        .join("\n");
      if (text) return text;
    }
  }
  return JSON.stringify(output, null, 2);
}

export type DevAssistTools = {
  list_projects: Tool;
  search_code: Tool;
  git_summary: Tool;
};

export type DevAssistSession = {
  client: MCPClient;
  tools: DevAssistTools;
  /** Tool names discovered from the remote server. */
  toolNames: string[];
};

/**
 * Open a Streamable HTTP session to remote DevAssist and build AI SDK tools.
 *
 * Caller must `await session.client.close()` when the agent run finishes.
 */
export async function connectDevAssist(
  config: HarnessConfig,
): Promise<DevAssistSession> {
  const client = await createMCPClient({
    transport: {
      type: "http",
      url: config.devassistUrl,
      headers: {
        Authorization: `Bearer ${config.devassistApiKey}`,
      },
    },
  });

  try {
    // Explicit Zod schemas: zero-arg MCP tools fail AI SDK validation under
    // schema-discovery alone. Docs recommend z.object({}) for no-arg tools.
    const mcpTools = await client.tools({
      schemas: {
        list_projects: {
          inputSchema: z.object({}),
        },
        search_code: {
          inputSchema: z.object({
            project: z
              .string()
              .describe("Project directory name under WORKSPACE_ROOT"),
            query: z
              .string()
              .describe("Substring to search for in project files"),
          }),
        },
        git_summary: {
          inputSchema: z.object({
            project: z
              .string()
              .describe("Project directory name under WORKSPACE_ROOT"),
          }),
        },
      },
    });

    const toolNames = Object.keys(mcpTools);
    for (const name of ["list_projects", "search_code", "git_summary"]) {
      if (!toolNames.includes(name)) {
        throw new Error(
          `Remote DevAssist missing expected tool "${name}". Got: ${toolNames.join(", ")}`,
        );
      }
    }

    // Re-wrap execute → plain text so the model sees readable results and we
    // avoid a CallToolResult / toModelOutput edge case in this SDK combo.
    const tools: DevAssistTools = {
      list_projects: tool({
        description:
          mcpTools.list_projects.description ??
          "List development projects under WORKSPACE_ROOT.",
        inputSchema: z.object({}),
        execute: async (_args, opts) =>
          textFromMcp(await mcpTools.list_projects.execute({}, opts)),
      }),
      search_code: tool({
        description:
          mcpTools.search_code.description ??
          "Search project source files for a substring.",
        inputSchema: z.object({
          project: z
            .string()
            .describe("Project directory name under WORKSPACE_ROOT"),
          query: z
            .string()
            .describe("Substring to search for in project files"),
        }),
        execute: async (args, opts) =>
          textFromMcp(await mcpTools.search_code.execute(args, opts)),
      }),
      git_summary: tool({
        description:
          mcpTools.git_summary.description ??
          "Summarize git status for a project.",
        inputSchema: z.object({
          project: z
            .string()
            .describe("Project directory name under WORKSPACE_ROOT"),
        }),
        execute: async (args, opts) =>
          textFromMcp(await mcpTools.git_summary.execute(args, opts)),
      }),
    };

    return { client, tools, toolNames: Object.keys(tools) };
  } catch (err) {
    await client.close().catch(() => undefined);
    throw err;
  }
}
