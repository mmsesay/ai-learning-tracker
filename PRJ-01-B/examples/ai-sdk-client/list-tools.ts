/**
 * Discover remote DevAssist MCP tools (no LLM).
 *
 *   DEVASSIST_API_KEY=... npm run list-tools
 */

import "dotenv/config";
import { Agent, setGlobalDispatcher } from "undici";
import { createMCPClient } from "@ai-sdk/mcp";

// Render free-tier cold starts often exceed undici's default 10s connect timeout.
// Prefer IPv4 — some networks stall on IPv6 routes to Render.
setGlobalDispatcher(new Agent({ connect: { timeout: 90_000, family: 4 } }));

const DEFAULT_URL = "https://ai-learning-tracker-c7m5.onrender.com/mcp";

async function main() {
  if (!process.env.DEVASSIST_API_KEY?.trim() && process.env.API_KEY?.trim()) {
    process.env.DEVASSIST_API_KEY = process.env.API_KEY;
  }

  const url = process.env.DEVASSIST_URL ?? DEFAULT_URL;
  const apiKey = process.env.DEVASSIST_API_KEY;

  if (!apiKey) {
    throw new Error("Set DEVASSIST_API_KEY (Bearer token for remote /mcp).");
  }

  console.log(`Connecting to ${url} …`);

  const mcpClient = await createMCPClient({
    transport: {
      type: "http",
      url,
      headers: { Authorization: `Bearer ${apiKey}` },
    },
  });

  try {
    const tools = await mcpClient.tools();
    const names = Object.keys(tools);
    console.log("Discovered MCP tools:", names.join(", "));
    if (!names.includes("list_projects") || !names.includes("search_code")) {
      throw new Error("Expected list_projects and search_code from DevAssist.");
    }
  } finally {
    await mcpClient.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
