/**
 * AI SDK → remote DevAssist MCP (Streamable HTTP on Render).
 *
 * Flow:
 *   User prompt → generateText → MCP tools → HTTPS → Render /mcp
 *
 *   cd examples/ai-sdk-client
 *   cp .env.example .env   # set DEVASSIST_API_KEY + OPENAI_ or OPENROUTER_ key
 *   npm install
 *   npm start
 */

import "dotenv/config";
import { Agent, setGlobalDispatcher } from "undici";
import { createMCPClient } from "@ai-sdk/mcp";
import { createOpenAI } from "@ai-sdk/openai";
import { generateText, stepCountIs, tool } from "ai";
import { z } from "zod";

// Render free-tier cold starts often exceed undici's default 10s connect timeout.
// Prefer IPv4 — some networks stall on IPv6 routes to Render.
setGlobalDispatcher(new Agent({ connect: { timeout: 90_000, family: 4 } }));

const DEFAULT_URL = "https://ai-learning-tracker-c7m5.onrender.com/mcp";

function requireEnv(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

/**
 * OpenAI or OpenRouter (OpenAI-compatible) — never hard-code keys.
 *
 * Use `.chat()` so OpenRouter hits Chat Completions. The default Responses API
 * path can hang or mis-handle tool rounds with free routers.
 */
function createModel() {
  const openrouterKey = process.env.OPENROUTER_API_KEY?.trim();
  if (openrouterKey) {
    const openrouter = createOpenAI({
      apiKey: openrouterKey,
      baseURL: process.env.OPENAI_BASE_URL || "https://openrouter.ai/api/v1",
    });
    // Prefer a tool-capable free model; openrouter/free is flaky with MCP tools.
    const id =
      process.env.OPENAI_MODEL || "google/gemma-4-26b-a4b-it:free";
    return openrouter.chat(id);
  }

  const openaiKey = process.env.OPENAI_API_KEY?.trim();
  if (openaiKey) {
    const openai = createOpenAI({ apiKey: openaiKey });
    return openai.chat(process.env.OPENAI_MODEL || "gpt-4o-mini");
  }

  throw new Error(
    "Set OPENROUTER_API_KEY or OPENAI_API_KEY so generateText can call a model.",
  );
}

/** Flatten MCP CallToolResult (or plain string) into model-readable text. */
function textFromMcp(output: unknown): string {
  if (typeof output === "string") return output;
  if (output && typeof output === "object") {
    const content = (output as { content?: Array<{ type?: string; text?: string }> })
      .content;
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

async function main() {
  // Accept Render's API_KEY as a fallback name when copying from PRJ-01-B/.env.
  if (!process.env.DEVASSIST_API_KEY?.trim() && process.env.API_KEY?.trim()) {
    process.env.DEVASSIST_API_KEY = process.env.API_KEY;
  }

  const url = process.env.DEVASSIST_URL ?? DEFAULT_URL;
  const apiKey = requireEnv("DEVASSIST_API_KEY");
  const prompt =
    process.argv.slice(2).join(" ").trim() ||
    "List the projects available in my workspace. Then search the sample-app project for the word greet.";

  console.log("=== DevAssist AI SDK client ===");
  console.log(`MCP URL: ${url}`);
  console.log(`Prompt:  ${prompt}`);
  console.log("");

  // Streamable HTTP to the remote Render MCP endpoint (not a local server).
  const mcpClient = await createMCPClient({
    transport: {
      type: "http",
      url,
      headers: { Authorization: `Bearer ${apiKey}` },
    },
  });

  try {
    // Explicit Zod schemas: empty MCP schemas (list_projects) fail AI SDK
    // input validation under schema-discovery alone ("value is not a function").
    // Docs recommend defining schemas for zero-arg tools as z.object({}).
    const mcpTools = await mcpClient.tools({
      schemas: {
        list_projects: {
          inputSchema: z.object({}),
        },
        search_code: {
          inputSchema: z.object({
            project: z
              .string()
              .describe("Project directory name under WORKSPACE_ROOT"),
            query: z.string().describe("Substring to search for in project files"),
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

    // Re-wrap execute to return plain text. Raw CallToolResult + toModelOutput
    // can crash mid-round in this SDK combo when output is briefly undefined.
    const tools = {
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
          query: z.string().describe("Substring to search for in project files"),
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

    const toolNames = Object.keys(tools);
    console.log("Discovered tools:", toolNames.join(", "));
    console.log("");

    const result = await generateText({
      model: createModel(),
      tools,
      // Allow the model to call tools then answer (multi-step).
      stopWhen: stepCountIs(6),
      maxRetries: 1,
      abortSignal: AbortSignal.timeout(120_000),
      system:
        "You are a concise assistant. Prefer DevAssist MCP tools over guessing. " +
        "When listing projects or searching code, call the matching tools. " +
        "Quote paths from tool results so we can see they came from the remote server.",
      prompt,
    });

    console.log("=== Tool calls ===");
    for (const step of result.steps) {
      for (const call of step.toolCalls) {
        if ("invalid" in call && call.invalid) {
          console.log(
            `→ ${call.toolName} INVALID: ${String((call as { error?: unknown }).error)}`,
          );
          continue;
        }
        console.log(`→ ${call.toolName}(${JSON.stringify(call.input)})`);
      }
      for (const tr of step.toolResults) {
        console.log(`← ${tr.toolName}:\n${String(tr.output)}\n`);
      }
    }

    console.log("=== Final answer ===");
    console.log(result.text || "(empty text)");

    // Sanity: remote Render paths show up in tool output.
    const blob = JSON.stringify(result.steps);
    if (blob.includes("/opt/render/")) {
      console.log(
        "\n[ok] Tool output references /opt/render/ (remote Render filesystem).",
      );
    } else if (blob.includes("list_projects") || blob.includes("sample-app")) {
      console.log("\n[ok] Tool output looks like DevAssist results.");
    } else {
      console.log(
        "\n[warn] Did not see /opt/render/ in tool results — check MCP URL.",
      );
    }
  } finally {
    await mcpClient.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
