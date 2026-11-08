# Copilot & Agent Instructions for FlexyGram

Follow all instructions specified in [AGENTS.md](../AGENTS.md).

Key guidelines:
1. Always base work on branch `codex/flexygram-beta-glass`.
2. Current active version: `1.0.0-beta.20` (Build `1309`).
3. App package: `com.flexygram.messenger`.
4. Compilation is handled via GitHub Actions workflow `ui-beta-debug.yml`. Never attempt local full gradle compilation in a chat sandbox.
5. All custom FlexyGram code resides under `TMessagesProj/src/main/java/app/flexygram/` and UI overrides in `TMessagesProj/src/main/java/org/telegram/ui/`.
