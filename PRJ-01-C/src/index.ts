/**
 * CLI entry for PRJ-01-C — Agent Harness.
 *
 * Usage:
 *   npm start "List the projects available in my workspace"
 *   npm run list-tools
 */

import { loadConfig } from "./config.js";
import { runAgent } from "./agent.js";
import { connectDevAssist } from "./mcp.js";

const BANNER = `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRJ-01-C — Agent Harness
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`;

async function listToolsOnly(): Promise<void> {
  const config = loadConfig();
  console.log(BANNER);
  console.log(`\nConnecting to ${config.devassistUrl} …`);
  const session = await connectDevAssist(config);
  try {
    console.log(`Discovered tools: ${session.toolNames.join(", ")}`);
  } finally {
    await session.client.close();
  }
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);

  if (args.includes("--list-tools") || args[0] === "list-tools") {
    await listToolsOnly();
    return;
  }

  const task = args.join(" ").trim();
  if (!task) {
    console.error(
      'Usage: npm start "<task>"\n' +
        'Example: npm start "List the projects available in my workspace"',
    );
    process.exit(1);
  }

  console.log(BANNER);
  console.log("\nTask:");
  console.log(task);

  const config = loadConfig();
  const result = await runAgent(config, task);

  console.log("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log("\nFinal answer:");
  console.log(result.text);
  console.log(
    `\n(steps used: ${result.stepsUsed} / max ${result.maxSteps})`,
  );

  if (result.sawRemoteRenderPath) {
    console.log(
      "[ok] Tool output references /opt/render/ (remote Render filesystem).",
    );
  } else {
    console.log(
      "[warn] Did not see /opt/render/ in tool results — check DEVASSIST_URL.",
    );
  }
}

main().catch((err: unknown) => {
  // Never dump secrets; keep errors readable for learning.
  const message = err instanceof Error ? err.message : String(err);
  console.error("\nHarness error:");
  console.error(message);
  process.exit(1);
});
