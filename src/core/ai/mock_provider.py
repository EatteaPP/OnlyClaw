from __future__ import annotations

from typing import Any

from src.core.intent import (
    contains_unsafe_scheme,
    extract_browser,
    extract_first_url,
    extract_registered_app,
)

from .provider import AiProvider


class MockAiProvider(AiProvider):
    def complete(self, prompt: str, *, system: str | None = None) -> str:
        del system
        return f"[mock] {prompt}"

    def classify_intent(self, command: str, skill_index: list[dict[str, Any]]) -> dict[str, Any]:
        if contains_unsafe_scheme(command):
            return {
                "status": "capability_not_available",
                "intent": None,
                "skill_name": None,
                "confidence": 0.0,
                "parameters": {},
                "message": "The command contains an unsafe URL scheme and cannot be opened.",
            }

        skill_names = {str(skill.get("name", "")).strip().lower(): skill for skill in skill_index}
        open_url_skill = skill_names.get("open-url")
        open_app_skill = skill_names.get("open-app")

        url = extract_first_url(command)
        if url and open_url_skill is not None:
            return {
                "status": "matched",
                "intent": "run_skill",
                "skill_name": "open-url",
                "confidence": 0.95,
                "parameters": {
                    "url": url,
                    "browser": extract_browser(command),
                },
                "message": "Mock matched open-url skill",
            }

        app, matched_alias = extract_registered_app(command, skill_index)
        if app and open_app_skill is not None:
            return {
                "status": "matched",
                "intent": "run_skill",
                "skill_name": "open-app",
                "confidence": 0.95,
                "parameters": {
                    "app": app,
                },
                "message": f"Matched open-app by registered app alias: {matched_alias}",
            }

        command_lower = command.lower()
        for skill in skill_index:
            name = str(skill.get("name", "")).strip()
            triggers = skill.get("triggers", [])
            if not name:
                continue

            if name.lower() in command_lower:
                return {
                    "status": "matched",
                    "intent": "run_skill",
                    "skill_name": name,
                    "confidence": 0.9,
                    "parameters": {},
                    "message": f"Mock matched skill: {name}",
                }

            for trigger in triggers:
                trigger_text = str(trigger).strip()
                if trigger_text and trigger_text.lower() in command_lower:
                    return {
                        "status": "matched",
                        "intent": "run_skill",
                        "skill_name": name,
                        "confidence": 0.8,
                        "parameters": {},
                        "message": f"Mock matched trigger: {trigger_text}",
                    }

        return {
            "status": "capability_not_available",
            "intent": None,
            "skill_name": None,
            "confidence": 0.0,
            "parameters": {},
            "message": "目前沒有符合的 app alias。No Skill, No Action.",
        }

    def summarize_result(self, command: str, result: dict[str, Any]) -> str:
        del command

        status = str(result.get("status", ""))
        execution = result.get("execution")
        skill = result.get("skill")
        skill_name = ""

        if isinstance(skill, dict):
            skill_name = str(skill.get("name", "")).strip()
        if not skill_name:
            skill_name = str(result.get("skill_name", "")).strip()

        if status == "capability_not_available":
            return "目前沒有符合的 skill。No Skill, No Action. 請建立新的 skill + script + executor."

        if isinstance(execution, dict):
            success = bool(execution.get("success", False))
            message = str(execution.get("message", "")).strip()
            if success:
                return f"已執行 {skill_name}：{message}" if skill_name else message
            return f"執行 {skill_name} 失敗：{message}" if skill_name else message

        if status == "matched":
            return f"已處理 {skill_name}。" if skill_name else "已處理指令。"

        message = str(result.get("message", "")).strip()
        if message:
            return message
        return "目前沒有符合的 skill。No Skill, No Action. 請建立新的 skill + script + executor."
