# Personal Command Widget

A small Windows desktop command widget for personal AI-assisted workflows.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
copy config.example.yaml config.yaml
python .\src\main.py
```

## First version

- Tray resident floating window
- YAML config with defaults and reload
- Double-Ctrl hotkey toggle
- Command router, skill registry, executor stubs
- AI provider interface with mock/OpenAI/Gemini backends
- Workspace skill discovery from `workspace/skills/*/skill.yaml`
- Built-in `open-app` and `open-url` skills

## Skills

Skills live under `workspace/skills/`.

Each skill contains:

- `SKILL.md`
- `skill.yaml`
- `scripts/`
- `examples/`

Built-in skills in this version:

- `open-app`
- `open-url`

Triggers are declared in `skill.yaml` and used by the AI provider to map a command to a registered skill.

## Execution

OnlyClaw routes every command through:

`Skill Registry` -> `Executor` -> `Script` -> `Structured Result`

The executor only supports Python scripts in this version.

## AI Providers

OnlyClaw currently supports:

- `mock`
- `openai`
- `gemini`

Set the provider in `.env`:

```env
ONLYCLAW_AI_PROVIDER=mock
```

OpenAI:

```env
ONLYCLAW_AI_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-5.4-mini
```

Gemini:

```env
ONLYCLAW_AI_PROVIDER=gemini
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash
```

If provider setup fails, OnlyClaw falls back to the mock provider.

## Security Rules

OnlyClaw must not:

- execute arbitrary shell commands
- use `shell=True`
- execute unregistered skills
- open unsupported URL schemes
- automate browsers after launch
- click UI elements
- submit forms
- log into websites

Execution logs are written to `workspace/logs/YYYY-MM-DD.log`.

## System Tray

OnlyClaw runs in the Windows system tray.

Tray menu:
- Show / Hide
- Reload Config
- Exit

Use Exit to fully quit the application.
