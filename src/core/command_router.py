from __future__ import annotations

from typing import Any

from src.core.ai.provider_factory import create_ai_provider
from src.core.executor import Executor
from src.core.skill_registry import SkillRegistry


class CommandRouter:
    def __init__(self, workspace_path: str, config: dict[str, Any] | None = None):
        self.workspace_path = workspace_path
        self.config = config or {}
        self.skill_registry = SkillRegistry(workspace_path)
        self.executor = Executor(workspace_path)
        self.ai_provider = create_ai_provider(self.config)
        skills_config = self.config.get("skills", {})
        self.auto_execute_permissions = set(skills_config.get("auto_execute_permissions", []))
        self.require_approval_permissions = set(skills_config.get("require_approval_permissions", []))

    def _missing_required_parameter(
        self,
        command: str,
        skill_name: str,
        parameters: dict[str, Any],
        required_key: str,
    ) -> dict[str, Any]:
        return {
            "status": "error",
            "command": command,
            "intent": {
                "status": "matched",
                "intent": "run_skill",
                "skill_name": skill_name,
                "confidence": 1.0,
                "parameters": parameters,
                "message": f"{skill_name} skill matched, but required parameter '{required_key}' is missing.",
            },
            "skills": [],
            "message": f"{skill_name} skill 已匹配，但缺少必要參數 {required_key}。",
            "debug": {
                "skill_name": skill_name,
                "parameters": parameters,
            },
            "summary": f"{skill_name} skill 已匹配，但缺少必要參數 {required_key}。",
        }

    def handle(self, command: str) -> dict[str, Any]:
        skills_config = self.config.get("skills", {})
        if isinstance(skills_config, dict) and not bool(skills_config.get("enabled", True)):
            return {
                "status": "capability_not_available",
                "command": command,
                "intent": None,
                "skills": [],
                "message": "Skills are disabled in configuration.",
                "summary": "目前沒有符合的 skill。No Skill, No Action. 請建立新的 skill + script + executor.",
            }

        skills = self.skill_registry.list_skills()
        intent = self.ai_provider.classify_intent(command, skills)

        if not isinstance(intent, dict):
            return {
                "status": "error",
                "command": command,
                "message": "AI provider returned an invalid intent payload.",
                "intent": None,
                "skills": skills,
                "summary": "AI provider returned an invalid intent payload.",
            }

        status = str(intent.get("status", "error"))
        if status == "matched":
            skill_name = str(intent.get("skill_name", "")).strip()
            skill = self.skill_registry.get_skill(skill_name)
            if skill is None:
                return {
                    "status": "error",
                    "command": command,
                    "intent": intent,
                    "skills": skills,
                    "message": f"Matched skill '{skill_name}' was not found in the registry.",
                    "summary": f"Matched skill '{skill_name}' was not found in the registry.",
                }

            if not bool(skill.get("enabled", True)):
                return {
                    "status": "error",
                    "command": command,
                    "intent": intent,
                    "skill": skill,
                    "skills": skills,
                    "message": f"Skill '{skill_name}' is disabled.",
                    "summary": f"Skill '{skill_name}' is disabled.",
                }

            permission = str(skill.get("permission", "")).strip()
            if permission in self.require_approval_permissions:
                return {
                    "status": "approval_required",
                    "command": command,
                    "intent": intent,
                    "skill": skill,
                    "skills": skills,
                    "message": f"Permission '{permission}' requires approval before execution.",
                    "summary": f"Permission '{permission}' requires approval before execution.",
                }

            if permission not in self.auto_execute_permissions:
                return {
                    "status": "error",
                    "command": command,
                    "intent": intent,
                    "skill": skill,
                    "skills": skills,
                    "message": f"Permission '{permission}' is not auto-executable.",
                    "summary": f"Permission '{permission}' is not auto-executable.",
                }

            parameters = intent.get("parameters", {})
            if not isinstance(parameters, dict):
                parameters = {}

            if skill_name == "open-url" and not str(parameters.get("url", "")).strip():
                return self._missing_required_parameter(command, "open-url", parameters, "url")

            if skill_name == "open-app" and not str(parameters.get("app", "")).strip():
                return self._missing_required_parameter(command, "open-app", parameters, "app")

            execution = self.executor.execute(skill_name, parameters, skill=skill, command=command)
            summary = self.ai_provider.summarize_result(
                command,
                {
                    "intent": intent,
                    "skill": skill,
                    "execution": execution,
                    "skill_name": skill_name,
                },
            )
            return {
                "status": "matched",
                "command": command,
                "intent": intent,
                "skill": skill,
                "execution": execution,
                "summary": summary,
                "skills": skills,
            }

        if status == "capability_not_available":
            summary = "目前沒有符合的 skill。No Skill, No Action. 請建立新的 skill + script + executor."
            return {
                "status": "capability_not_available",
                "command": command,
                "intent": intent,
                "skills": skills,
                "message": str(intent.get("message", summary)),
                "summary": summary,
            }

        summary = str(intent.get("message", "AI provider returned an error."))
        return {
            "status": "error",
            "command": command,
            "intent": intent,
            "skills": skills,
            "message": summary,
            "summary": summary,
        }
