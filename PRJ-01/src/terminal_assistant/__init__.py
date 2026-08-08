"""AI Terminal Assistant (TAM) — local CLI agent with tool calling.

Developer: Maej

Package layout (read in this order while learning):
  config.py  → load API key / model / workspace
  tools.py   → schemas + Python tool implementations
  agent.py   → the agent loop (model ↔ tools)
  main.py    → Typer/Rich REPL
"""

__version__ = "0.1.0"
__author__ = "Maej"
