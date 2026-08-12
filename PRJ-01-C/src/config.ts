/**
 * Load and validate harness settings from the environment.
 *
 * Fits the project as the single place for URLs, keys, model id, and step caps —
 * never hard-code secrets; never print API keys.
 */

import "dotenv/config";

const DEFAULT_MCP_URL =
  "https://ai-learning-tracker-c7m5.onrender.com/mcp";
const DEFAULT_MODEL = "google/gemma-4-26b-a4b-it:free";
const DEFAULT_BASE_URL = "https://openrouter.ai/api/v1";
const DEFAULT_MAX_STEPS = 6;

export type HarnessConfig = {
  /** Remote DevAssist Streamable HTTP endpoint. */
  devassistUrl: string;
  /** Bearer token for /mcp (same value as Render API_KEY). */
  devassistApiKey: string;
  /** OpenRouter API key. */
  openrouterApiKey: string;
  /** OpenAI-compatible base URL (OpenRouter by default). */
  openaiBaseUrl: string;
  /** Model id on OpenRouter. */
  openaiModel: string;
  /**
   * Maximum generateText steps (each step is one model call that may include
   * tool calls). Prevents infinite agent loops.
   */
  maxSteps: number;
};

function requireEnv(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

/**
 * Read env vars into a typed config object.
 *
 * Accepts `API_KEY` as a fallback for `DEVASSIST_API_KEY` when copying from
 * PRJ-01-B/.env (never log the value).
 */
export function loadConfig(): HarnessConfig {
  if (!process.env.DEVASSIST_API_KEY?.trim() && process.env.API_KEY?.trim()) {
    process.env.DEVASSIST_API_KEY = process.env.API_KEY;
  }

  const maxStepsRaw = process.env.MAX_STEPS?.trim();
  const maxSteps = maxStepsRaw
    ? Number.parseInt(maxStepsRaw, 10)
    : DEFAULT_MAX_STEPS;

  if (!Number.isFinite(maxSteps) || maxSteps < 1) {
    throw new Error(`MAX_STEPS must be a positive integer (got ${maxStepsRaw})`);
  }

  return {
    devassistUrl: process.env.DEVASSIST_URL?.trim() || DEFAULT_MCP_URL,
    devassistApiKey: requireEnv("DEVASSIST_API_KEY"),
    openrouterApiKey: requireEnv("OPENROUTER_API_KEY"),
    openaiBaseUrl: process.env.OPENAI_BASE_URL?.trim() || DEFAULT_BASE_URL,
    openaiModel: process.env.OPENAI_MODEL?.trim() || DEFAULT_MODEL,
    maxSteps,
  };
}
