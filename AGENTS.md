# Personal Command Widget - Agent Rules

## Core Principle

No Skill, No Action.

This application is a controlled personal command launcher.  
The AI must not directly operate the computer or execute arbitrary shell commands.

## Rules

1. AI may only execute registered skills.
2. If no matching skill exists, AI must report that it does not have the capability.
3. AI must not invent browser automation steps by itself.
4. AI must not execute arbitrary PowerShell, cmd, Python, or shell commands.
5. AI must not approve, reject, submit, merge, deploy, delete, or send anything unless a registered skill explicitly supports it and user approval is required.
6. All future skill execution must go through the Executor layer.
7. All future skill execution should produce structured output.
8. All future dangerous actions must be disabled by default.

## First Version Scope

The first version only implements:
- Floating desktop window
- Config loading
- Hotkey toggle
- System tray
- Command router stub
- Skill registry stub
- Executor stub