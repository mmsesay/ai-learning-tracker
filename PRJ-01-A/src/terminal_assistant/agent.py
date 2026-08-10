"""Agent loop: talk to the LLM, run tools, feed results back.

This is the heart of tool calling:

1. Send conversation + tool schemas to the model
2. If the model returns tool_calls, execute them in Python
3. Append tool results to the conversation
4. Call the model again until it answers in plain text

That loop is what turns a chat model into an agent.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from openai import OpenAI
from rich.console import Console

from terminal_assistant.config import Settings
from terminal_assistant.tools import CONFIRM_TOOLS, TOOL_SCHEMAS, dispatch_tool

# Instructions the model sees on every turn (role=system).
# Identity facts stay here so TAM can answer “who built you?” without showing
# that branding on every startup banner.


def build_system_prompt(settings: Settings) -> str:
    """Build the system prompt, including live model/workspace facts."""
    provider = (
        "OpenRouter (OpenAI-compatible API)"
        if settings.base_url and "openrouter.ai" in settings.base_url
        else "OpenAI-compatible API"
    )
    return f"""You are TAM — AI Terminal Assistant, a local CLI agent.

About you (answer only if the user asks; do not volunteer this unprompted):
- Name: AI Terminal Assistant (TAM). CLI commands: `tam` or `terminal-assistant`.
- Who built it: Maej (Muhammad Sesay).
- Why: Learning project (PRJ-01-A) to practice LLM tool calling, agent loops, JSON schemas, and safe local tools — first step on Maej's AI engineering roadmap.
- When: Started August 2026 as Project 1 on that roadmap.
- How you work: Chat Completions with tools. You may call tools; Python runs them on the user's machine; results return as tool messages; you loop until you can answer in plain text. Risky tools (write_file, execute_shell_command) require the user's confirmation.
- What model you are using right now: `{settings.model}` via {provider}.
- Workspace root for this session: `{settings.workspace}`.
- Tools you have: list_files, read_file, search_text, write_file, execute_shell_command, git_status.

About Maej (answer when asked who Maej is / who built you / about the developer):
- Full name: Muhammad Sesay; goes by Maej.
- Role: Full-stack web developer and Pythonista; building toward AI engineering.
- Company: Nexlura.
- Location: Freetown, Sierra Leone.
- Stack: Go, Python, Flask, TypeScript, React, Next.js; also learning AI agents, LLMs, and tool calling.
- Interests: coding, gaming, art; open to new opportunities.
- Links: https://maej.dev · GitHub https://github.com/mmsesay · X/Twitter @DeeMaejor
- This repo: https://github.com/mmsesay/ai-learning-tracker (TAM lives in PRJ-01-A; Weather MCP in PRJ-01-B).
- Do not invent extra personal details beyond this. If asked something unknown, say you only know what's in your context.

Rules:
- Prefer tools over guessing about files or the filesystem.
- Paths are relative to the workspace root.
- Be concise. After using tools, answer the user's question clearly.
- For write_file and execute_shell_command, the user must approve before they run.
- Do not invent file contents you have not read.
"""


# Callback types so the CLI can print tools / ask for confirmation without
# coupling this module to Rich/Typer.
ConfirmFn = Callable[[str, dict[str, Any]], bool]
OnToolFn = Callable[[str, dict[str, Any]], None]


class TerminalAgent:
    """Stateful multi-turn agent that keeps a chat history and runs tools."""

    def __init__(
        self,
        settings: Settings,
        console: Console | None = None,
        confirm: ConfirmFn | None = None,
        on_tool: OnToolFn | None = None,
    ) -> None:
        self.settings = settings
        self.console = console or Console()
        # Defaults allow unit-testing without interactive prompts
        self.confirm = confirm or (lambda _name, _args: True)
        self.on_tool = on_tool or (lambda _name, _args: None)

        # OpenAI SDK works with OpenRouter when base_url points at openrouter.ai
        client_kwargs: dict[str, Any] = {"api_key": settings.api_key}
        if settings.base_url:
            client_kwargs["base_url"] = settings.base_url
        if settings.base_url and "openrouter.ai" in settings.base_url:
            # Optional OpenRouter attribution headers (recommended by their docs)
            client_kwargs["default_headers"] = {
                "HTTP-Referer": "https://github.com/local/ai-terminal-assistant",
                "X-Title": "AI Terminal Assistant (TAM)",
            }
        self.client = OpenAI(**client_kwargs)

        # Conversation memory for this session. Every turn appends here so the
        # model can use earlier tool results (context management).
        self._system_prompt = build_system_prompt(settings)
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._system_prompt},
        ]

    def clear_history(self) -> None:
        """Reset chat memory but keep the system prompt."""
        self.messages = [{"role": "system", "content": self._system_prompt}]

    def run_turn(self, user_text: str) -> str:
        """Process one user message; may call tools multiple times.

        Returns the model's final plain-text answer for this turn.
        """
        self.messages.append({"role": "user", "content": user_text})

        # --- Agent loop -------------------------------------------------
        # Cap iterations so a confused model cannot call tools forever.
        for _ in range(self.settings.max_iterations):
            # 1) Ask the model what to do next (answer OR call tools)
            response = self.client.chat.completions.create(
                model=self.settings.model,
                messages=self.messages,
                tools=TOOL_SCHEMAS,  # JSON schemas describing available tools
                tool_choice="auto",  # model decides whether to call a tool
            )
            message = response.choices[0].message

            # 2) Persist the assistant message (must include tool_calls if any,
            #    otherwise the next request is invalid / the model loses context)
            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": message.content or "",
            }
            if message.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments or "{}",
                        },
                    }
                    for tc in message.tool_calls
                ]
            self.messages.append(assistant_msg)

            # 3) No tool calls → this is the final natural-language answer
            if not message.tool_calls:
                return (message.content or "").strip() or "(no response)"

            # 4) Execute each requested tool and append role=tool results
            for tc in message.tool_calls:
                name = tc.function.name
                raw_args = tc.function.arguments or "{}"
                try:
                    args = json.loads(raw_args)
                except json.JSONDecodeError:
                    args = {"_raw": raw_args}

                # Let the CLI show "→ list_files(...)" so you can watch the loop
                self.on_tool(name, args if isinstance(args, dict) else {"_raw": raw_args})

                # Safety: writes / shell need human approval before side effects
                if name in CONFIRM_TOOLS:
                    ok = self.confirm(name, args if isinstance(args, dict) else {})
                    if not ok:
                        result = "User declined this action. Do not retry unless they ask again."
                        self.messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tc.id,  # must match the call id
                                "content": result,
                            }
                        )
                        continue

                result = dispatch_tool(name, raw_args, self.settings.workspace)
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    }
                )
            # Loop continues → model sees tool outputs and decides next step

        return (
            "Stopped: reached max tool iterations "
            f"({self.settings.max_iterations}). Try a more specific question."
        )
