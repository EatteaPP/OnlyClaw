from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class Executor:
    def __init__(self, workspace_path: str | None = None) -> None:
        self.workspace_path = Path(workspace_path) if workspace_path else None

    def _workspace_root(self, skill: dict[str, Any] | None = None) -> Path:
        if self.workspace_path is not None:
            return self.workspace_path
        if skill is not None:
            skill_dir = skill.get("skill_dir")
            if skill_dir:
                return Path(skill_dir).resolve().parents[1]
        return Path("workspace").resolve()

    def _log_directory(self, skill: dict[str, Any] | None = None) -> Path:
        return self._workspace_root(skill) / "logs"

    def _ensure_log_directory(self, skill: dict[str, Any] | None = None) -> Path:
        log_directory = self._log_directory(skill)
        log_directory.mkdir(parents=True, exist_ok=True)
        return log_directory

    def _write_log(self, skill_name: str, payload: dict[str, Any], skill: dict[str, Any] | None = None) -> Path:
        log_directory = self._ensure_log_directory(skill)
        log_path = log_directory / f"{datetime.now():%Y-%m-%d}.log"
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "skill_name": skill_name,
            **payload,
        }
        with log_path.open("a", encoding="utf-8") as file_handle:
            file_handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return log_path

    def _validate_skill(self, skill_name: str, skill: dict[str, Any] | None) -> tuple[dict[str, Any] | None, str | None]:
        if skill is None:
            return None, "Skill metadata is required for execution."

        if not bool(skill.get("enabled", True)):
            return None, f"Skill '{skill_name}' is disabled."

        skill_dir_value = str(skill.get("skill_dir", skill.get("path", ""))).strip()
        if not skill_dir_value:
            return None, f"Skill '{skill_name}' is missing a skill directory."

        skill_dir = Path(skill_dir_value).resolve()
        workspace_root = self._workspace_root(skill)
        allowed_skills_root = (workspace_root / "skills").resolve()
        if not skill_dir.is_relative_to(allowed_skills_root):
            return None, f"Skill directory is outside workspace skills: {skill_dir}"

        return skill, None

    def _safe_script_file(self, skill_dir: Path, script_path: str) -> Path | None:
        script_candidate = Path(script_path)
        if script_candidate.is_absolute():
            return None

        script_file = (skill_dir / script_candidate).resolve()
        try:
            script_file.relative_to(skill_dir)
        except ValueError:
            return None
        return script_file

    def _error_result(
        self,
        skill_name: str,
        message: str,
        params: dict[str, Any],
        skill: dict[str, Any] | None = None,
        *,
        command: str = "",
        stderr: str = "",
        stdout: str = "",
    ) -> dict[str, Any]:
        log_path = self._write_log(
            skill_name,
            {
                "command": command or skill_name,
                "params": params,
                "success": False,
                "message": message,
                "stdout": stdout,
                "stderr": stderr,
            },
            skill,
        )
        return {
            "status": "error",
            "success": False,
            "skill_name": skill_name,
            "params": params,
            "message": message,
            "data": None,
            "stdout": stdout,
            "stderr": stderr,
            "log_path": str(log_path),
        }

    def execute(
        self,
        skill_name: str,
        params: dict[str, Any],
        skill: dict[str, Any] | None = None,
        *,
        command: str = "",
    ) -> dict[str, Any]:
        validated_skill, validation_error = self._validate_skill(skill_name, skill)
        if validation_error is not None or validated_skill is None:
            return self._error_result(
                skill_name,
                validation_error or "Skill metadata is required for execution.",
                params,
                skill,
                command=command,
            )

        execution = validated_skill.get("execution", {})
        if not isinstance(execution, dict):
            execution = {}

        execution_type = str(execution.get("type", "")).strip().lower()
        if execution_type != "python":
            return self._error_result(
                skill_name,
                f"Unsupported execution type: {execution_type or 'unknown'}",
                params,
                validated_skill,
                command=command,
            )

        script_path = str(execution.get("script", "")).strip()
        if not script_path:
            return self._error_result(skill_name, "Missing execution script.", params, validated_skill, command=command)

        skill_dir = Path(str(validated_skill.get("skill_dir", validated_skill.get("path", "")))).resolve()
        script_file = self._safe_script_file(skill_dir, script_path)
        if script_file is None or not script_file.exists():
            return self._error_result(
                skill_name,
                f"Script not found or invalid: {skill_dir / script_path}",
                params,
                validated_skill,
                command=command,
            )

        timeout_seconds = int(execution.get("timeout_seconds", 10))
        process_input = json.dumps(params, ensure_ascii=False)

        try:
            completed = subprocess.run(
                [sys.executable, str(script_file)],
                input=process_input,
                capture_output=True,
                text=True,
                shell=False,
                cwd=str(skill_dir),
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            stderr = str(exc.stderr or "")
            stdout = str(exc.stdout or "")
            return self._error_result(
                skill_name,
                f"Execution timed out after {timeout_seconds} seconds.",
                params,
                validated_skill,
                command=command,
                stderr=stderr,
                stdout=stdout,
            )
        except Exception as exc:
            return self._error_result(skill_name, f"Failed to execute skill: {exc}", params, validated_skill, command=command)

        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()

        try:
            output = json.loads(stdout) if stdout else {}
        except json.JSONDecodeError:
            return self._error_result(
                skill_name,
                "Skill script returned invalid JSON.",
                params,
                validated_skill,
                command=command,
                stderr=stderr,
                stdout=stdout,
            )

        if not isinstance(output, dict):
            return self._error_result(
                skill_name,
                "Skill script returned a non-object JSON payload.",
                params,
                validated_skill,
                command=command,
                stderr=stderr,
                stdout=stdout,
            )

        success = bool(output.get("success", False))
        message = str(output.get("message", ""))
        data = output.get("data", {})
        if not isinstance(data, dict):
            data = {}

        log_path = self._write_log(
            skill_name,
            {
                "command": command or skill_name,
                "params": params,
                "success": success,
                "message": message,
                "stdout": stdout,
                "stderr": stderr,
                "data": data,
            },
            validated_skill,
        )

        return {
            "status": "executed" if success else "error",
            "success": success,
            "skill_name": skill_name,
            "params": params,
            "message": message,
            "data": data,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": completed.returncode,
            "log_path": str(log_path),
        }
