/**
 * Example: consume remote DevAssist MCP from the Vercel AI SDK.
 *
 * This is a *client* demo only — DevAssist itself stays a Python MCP server.
 *
 * Setup:
 *   cd examples/ai-sdk-client
 *   npm install
 *   export DEVASSIST_URL=https://YOUR-RAILWAY-DOMAIN/mcp
 *   export DEVASSIST_API_KEY=your-key   # if API_KEY is set on the server
 *   export OPENAI_API_KEY=...          # only needed if you call generateText
 *   npx tsx list-tools.ts
 */

import { createMCPClient } from "@ai-sdk/mcp";

async function main() {
  const url = process.env.DEVASSIST_URL ?? "http://127.0.0.1:3000/mcp";
  const apiKey = process.env.DEVASSIST_API_KEY;

  const mcpClient = await createMCPClient({
    transport: {
      type: "http",
      url,
      headers: apiKey
        ? { Authorization: `Bearer ${apiKey}` }
        : undefined,
    },
  });

  try {
    const tools = await mcpClient.tools();
    console.log("DevAssist tools:", Object.keys(tools));

    // Optional: wire into generateText when you have a model provider key.
    // import { generateText } from "ai";
    // import { openai } from "@ai-sdk/openai";
    // const result = await generateText({
    //   model: openai("gpt-4o-mini"),
    //   tools,
    //   prompt: "List my development projects.",
    // });
    // console.log(result.text);
  } finally {
    await mcpClient.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
