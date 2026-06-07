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

    def _empty_result(
        self,
        *,
        command: str,
        status: str,
        success: bool,
        message: str,
        intent: dict[str, Any] | None,
        skill: dict[str, Any] | None = None,
        execution: dict[str, Any] | None = None,
        debug: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = {
            "success": success,
            "status": status,
            "command": command,
            "intent": intent,
            "skill": skill,
            "execution": execution,
            "message": message,
            "summary": message,
            "skills": [],
        }
        if debug is not None:
            result["debug"] = debug
        return result

    def _missing_required_parameter(
        self,
        command: str,
        skill_name: str,
        parameters: dict[str, Any],
        required_key: str,
    ) -> dict[str, Any]:
        message = f"{skill_name} skill matched, but required parameter '{required_key}' is missing."
        return self._empty_result(
            command=command,
            status="error",
            success=False,
            message=message,
            intent={
                "status": "matched",
                "intent": "run_skill",
                "skill_name": skill_name,
                "confidence": 1.0,
                "parameters": parameters,
                "message": message,
            },
            debug={
                "skill_name": skill_name,
                "parameters": parameters,
            },
        )

    def handle(self, command: str) -> dict[str, Any]:
        skills_config = self.config.get("skills", {})
        if isinstance(skills_config, dict) and not bool(skills_config.get("enabled", True)):
            message = "Skills are disabled in configuration."
            return self._empty_result(
                command=command,
                status="capability_not_available",
                success=False,
                message=message,
                intent=None,
            )

        skills = self.skill_registry.list_skills()
        intent = self.ai_provider.classify_intent(command, skills)

        if not isinstance(intent, dict):
            message = "AI provider returned an invalid intent payload."
            result = self._empty_result(
                command=command,
                status="error",
                success=False,
                message=message,
                intent=None,
            )
            result["skills"] = skills
            return result

        status = str(intent.get("status", "error"))
        if status == "matched":
            skill_name = str(intent.get("skill_name", "")).strip()
            skill = self.skill_registry.get_skill(skill_name)
            if skill is None:
                message = f"Matched skill '{skill_name}' was not found in the registry."
                result = self._empty_result(
                    command=command,
                    status="error",
                    success=False,
                    message=message,
                    intent=intent,
                )
                result["skills"] = skills
                return result

            if not bool(skill.get("enabled", True)):
                message = f"Skill '{skill_name}' is disabled."
                result = self._empty_result(
                    command=command,
                    status="error",
                    success=False,
                    message=message,
                    intent=intent,
                    skill=skill,
                )
                result["skills"] = skills
                return result

            permission = str(skill.get("permission", "")).strip()
            if permission in self.require_approval_permissions:
                message = f"Permission '{permission}' requires approval before execution."
                result = self._empty_result(
                    command=command,
                    status="approval_required",
                    success=False,
                    message=message,
                    intent=intent,
                    skill=skill,
                )
                result["skills"] = skills
                return result

            if permission not in self.auto_execute_permissions:
                message = f"Permission '{permission}' is not auto-executable."
                result = self._empty_result(
                    command=command,
                    status="error",
                    success=False,
                    message=message,
                    intent=intent,
                    skill=skill,
                )
                result["skills"] = skills
                return result

            parameters = intent.get("parameters", {})
            if not isinstance(parameters, dict):
                parameters = {}

            if skill_name == "open-url" and not str(parameters.get("url", "")).strip():
                result = self._missing_required_parameter(command, "open-url", parameters, "url")
                result["skills"] = skills
                return result

            if skill_name == "open-app" and not str(parameters.get("app", "")).strip():
                result = self._missing_required_parameter(command, "open-app", parameters, "app")
                result["skills"] = skills
                return result

            execution = self.executor.execute(skill_name, parameters, skill=skill, command=command)
            execution_success = bool(execution.get("success", False)) if isinstance(execution, dict) else False
            message = ""
            if isinstance(execution, dict):
                message = str(execution.get("message", "")).strip()
            summary = self.ai_provider.summarize_result(
                command,
                {
                    "intent": intent,
                    "skill": skill,
                    "execution": execution,
                    "skill_name": skill_name,
                },
            )
            result = self._empty_result(
                command=command,
                status="executed" if execution_success else "error",
                success=execution_success,
                message=message or summary,
                intent=intent,
                skill=skill,
                execution=execution,
            )
            result["summary"] = summary
            result["skills"] = skills
            return result

        if status == "capability_not_available":
            message = str(intent.get("message", "No Skill, No Action.")).strip() or "No Skill, No Action."
            result = self._empty_result(
                command=command,
                status="capability_not_available",
                success=False,
                message=message,
                intent=intent,
            )
            result["skills"] = skills
            return result

        message = str(intent.get("message", "AI provider returned an error.")).strip() or "AI provider returned an error."
        result = self._empty_result(
            command=command,
            status="error",
            success=False,
            message=message,
            intent=intent,
        )
        result["skills"] = skills
        return result
