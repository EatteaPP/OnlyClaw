from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class SkillRegistry:
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)

    def _skills_root(self) -> Path:
        return self.workspace_path / "skills"

    def _load_skill_file(self, skill_file: Path) -> dict[str, Any] | None:
        try:
            with skill_file.open("r", encoding="utf-8") as file_handle:
                payload = yaml.safe_load(file_handle) or {}
        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"[skills] Warning: failed to read {skill_file}: {exc}")
            return None

        if not isinstance(payload, dict):
            return None

        name = str(payload.get("name", "")).strip()
        if not name:
            return None

        enabled = bool(payload.get("enabled", True))
        if not enabled:
            return None

        execution = payload.get("execution", {})
        if not isinstance(execution, dict):
            execution = {}

        parameters = payload.get("parameters", {})
        if not isinstance(parameters, dict):
            parameters = {}

        apps = payload.get("apps", {})
        if not isinstance(apps, dict):
            apps = {}

        triggers = payload.get("triggers", [])
        if isinstance(triggers, str):
            triggers = [triggers]
        if not isinstance(triggers, list):
            triggers = []

        return {
            "name": name,
            "description": str(payload.get("description", "")).strip(),
            "triggers": [str(trigger).strip() for trigger in triggers if str(trigger).strip()],
            "permission": str(payload.get("permission", "read-only")).strip() or "read-only",
            "parameters": parameters,
            "apps": apps,
            "execution": execution,
            "enabled": enabled,
            "path": str(skill_file.parent.resolve()),
            "skill_file": str(skill_file.resolve()),
            "skill_dir": str(skill_file.parent.resolve()),
        }

    def list_skills(self) -> list[dict[str, Any]]:
        skills_root = self._skills_root()
        if not skills_root.exists():
            return []

        skills: list[dict[str, Any]] = []
        for skill_file in sorted(skills_root.glob("*/skill.yaml")):
            skill = self._load_skill_file(skill_file)
            if skill is not None:
                skills.append(skill)
        return skills

    def get_skill(self, skill_name: str) -> dict[str, Any] | None:
        target_name = skill_name.strip().lower()
        if not target_name:
            return None

        for skill in self.list_skills():
            if str(skill.get("name", "")).strip().lower() == target_name:
                return skill
        return None
