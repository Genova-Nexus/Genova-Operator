"""ProjectInspector component for Genova Operator.

Builds structured project inspection reports analyzing directory trees,
dependencies, Git repositories, runtime environments, and entry points.
"""

from __future__ import annotations

import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from genova_operator.config.manager import ConfigManager
from genova_operator.core.exceptions import GenovaOperatorError
from genova_operator.core.interfaces import BaseComponent
from genova_operator.core.types import OperatorEvent, OperatorStatus
from genova_operator.inspector.models import (
    DependencySummary,
    DirectoryNode,
    DirectoryTree,
    EntryPointsSummary,
    EnvironmentInspection,
    ProjectInspectionReport,
    RepositoryInspection,
)
from genova_operator.registry.manager import ProjectRegistry
from genova_operator.registry.models import ProjectRecord
from genova_operator.workspace.manager import WorkspaceManager

logger = logging.getLogger(__name__)

KNOWN_FRAMEWORKS = [
    "torch", "tensorflow", "scikit-learn", "numpy", "pandas", "scipy",
    "fastapi", "flask", "django", "pytest", "requests", "pydantic", "transformers"
]


class ProjectInspector(BaseComponent):
    """Project Inspector component for Genova Operator.

    Inspects registered or discovered projects and builds detailed, structured
    ProjectInspectionReport objects.
    """

    def __init__(
        self,
        name: str = "project-inspector",
        project_registry: Optional[ProjectRegistry] = None,
        workspace_manager: Optional[WorkspaceManager] = None,
        config_manager: Optional[ConfigManager] = None,
    ) -> None:
        self._name = name
        self._project_registry = project_registry
        self._workspace_manager = workspace_manager
        self._config_manager = config_manager
        self._status = OperatorStatus.UNINITIALIZED

    @property
    def name(self) -> str:
        return self._name

    def initialize(self) -> None:
        """Initialize the ProjectInspector component."""
        logger.info("Initializing ProjectInspector (%s)...", self._name)
        self._status = OperatorStatus.READY
        logger.info("ProjectInspector initialized successfully.")

    def shutdown(self) -> None:
        """Shutdown ProjectInspector."""
        self._status = OperatorStatus.SHUTDOWN

    def get_status(self) -> OperatorStatus:
        return self._status

    def inspect_project(
        self,
        target: Union[str, ProjectRecord, Path],
        max_depth: int = 3,
    ) -> ProjectInspectionReport:
        """Inspect a target project and produce a comprehensive ProjectInspectionReport.

        Args:
            target: Project name, ProjectRecord, or directory Path.
            max_depth: Maximum directory tree recursion depth.

        Returns:
            ProjectInspectionReport instance.
        """
        logger.info("Starting inspection on target '%s'...", target)
        start_time = time.time()

        project_name, project_path, record = self._resolve_target(target)
        abs_path = Path(project_path).resolve()

        if not abs_path.exists() or not abs_path.is_dir():
            raise GenovaOperatorError(f"Cannot inspect project. Path '{abs_path}' does not exist or is not a directory.")

        tree = self.inspect_directory_tree(abs_path, max_depth=max_depth)
        dependencies = self.inspect_dependencies(abs_path)
        repository = self.inspect_repository(abs_path)
        environment = self.inspect_environment(abs_path, record=record)
        entry_points = self.inspect_entry_points(abs_path)

        metadata: Dict[str, Any] = {}
        if record:
            metadata["registered"] = True
            metadata["project_type"] = record.identity.project_type
        else:
            metadata["registered"] = False

        report = ProjectInspectionReport(
            project_name=project_name,
            project_path=str(abs_path),
            directory_tree=tree,
            dependencies=dependencies,
            repository=repository,
            environment=environment,
            entry_points=entry_points,
            metadata=metadata,
            inspected_at=time.time(),
        )

        logger.info("Inspection completed for project '%s' in %.3fs.", project_name, time.time() - start_time)
        return report

    def inspect_directory_tree(self, path: Path, max_depth: int = 3) -> DirectoryTree:
        """Build structured DirectoryTree representation for a directory."""
        total_files = 0
        total_dirs = 0
        total_size = 0

        def build_node(current_path: Path, rel_path: str, depth: int) -> DirectoryNode:
            nonlocal total_files, total_dirs, total_size

            node = DirectoryNode(
                name=current_path.name,
                path=rel_path or current_path.name,
                is_dir=current_path.is_dir(),
            )

            if current_path.is_dir():
                total_dirs += 1
                if depth < max_depth:
                    try:
                        for item in sorted(current_path.iterdir()):
                            if item.name.startswith((".", "_")) or item.name in ("dist", "build", "node_modules", "__pycache__"):
                                continue
                            child_rel = f"{rel_path}/{item.name}" if rel_path else item.name
                            node.children.append(build_node(item, child_rel, depth + 1))
                    except Exception:
                        pass
            else:
                total_files += 1
                try:
                    size = current_path.stat().st_size
                    node.size_bytes = size
                    total_size += size
                except Exception:
                    pass
                node.extension = current_path.suffix.lstrip(".")

            return node

        root_node = build_node(path, "", 0)
        return DirectoryTree(
            root_name=path.name,
            total_files=total_files,
            total_directories=total_dirs,
            total_size_bytes=total_size,
            root_node=root_node,
        )

    def inspect_dependencies(self, path: Path) -> DependencySummary:
        """Inspect and parse project dependencies from package files."""
        deps: List[str] = []
        frameworks: List[str] = []
        files_found: List[str] = []

        req_file = path / "requirements.txt"
        if req_file.is_file():
            files_found.append("requirements.txt")
            try:
                with open(req_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            pkg_name = re.split(r"[=<>]", line)[0].strip()
                            if pkg_name and pkg_name not in deps:
                                deps.append(pkg_name)
            except Exception:
                pass

        pyproject = path / "pyproject.toml"
        if pyproject.is_file():
            files_found.append("pyproject.toml")
            try:
                with open(pyproject, "r", encoding="utf-8") as f:
                    content = f.read()
                    matches = re.findall(r'["\']([a-zA-Z0-9_\-]+)[=<>]?', content)
                    for match in matches:
                        if match and match not in deps and len(match) > 2:
                            deps.append(match)
            except Exception:
                pass

        for dep in deps:
            dep_lower = dep.lower()
            for fw in KNOWN_FRAMEWORKS:
                if fw in dep_lower and fw not in frameworks:
                    frameworks.append(fw)

        return DependencySummary(
            dependencies=sorted(deps),
            frameworks=sorted(frameworks),
            package_files_found=files_found,
        )

    def inspect_repository(self, path: Path) -> RepositoryInspection:
        """Inspect Git repository status for a project directory."""
        git_dir = path / ".git"
        if not git_dir.exists():
            return RepositoryInspection(is_git_repo=False)

        branch: Optional[str] = None
        commit_hash: Optional[str] = None
        head_file = git_dir / "HEAD"
        if head_file.is_file():
            try:
                with open(head_file, "r", encoding="utf-8") as f:
                    head_content = f.read().strip()
                    if head_content.startswith("ref: refs/heads/"):
                        branch = head_content[len("ref: refs/heads/"):]
                    else:
                        commit_hash = head_content[:7]
            except Exception:
                pass

        return RepositoryInspection(
            is_git_repo=True,
            branch=branch or "main",
            commit_hash=commit_hash,
        )

    def inspect_environment(
        self,
        path: Path,
        record: Optional[ProjectRecord] = None,
    ) -> EnvironmentInspection:
        """Inspect runtime environment parameters."""
        env_type = "system"
        interpreter: Optional[str] = None

        if record and record.environment:
            env_type = record.environment.environment_type
            interpreter = record.environment.python_interpreter

        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        return EnvironmentInspection(
            environment_type=env_type,
            python_interpreter=interpreter or sys.executable,
            python_version=py_version,
            env_vars={"PYTHONPATH": str(path)},
        )

    def inspect_entry_points(self, path: Path) -> EntryPointsSummary:
        """Detect runnable scripts and entry points in project directory."""
        entry_scripts: Dict[str, str] = {}
        cli_commands: List[str] = []

        candidates = [
            ("main", "main.py"),
            ("app", "app.py"),
            ("train", "train.py"),
            ("eval", "eval.py"),
            ("run", "run.py"),
            ("cli", "cli.py"),
        ]

        for alias, rel in candidates:
            if (path / rel).is_file():
                entry_scripts[alias] = rel
            elif (path / "src" / rel).is_file():
                entry_scripts[alias] = f"src/{rel}"
            elif (path / "scripts" / rel).is_file():
                entry_scripts[alias] = f"scripts/{rel}"

        has_tests = (path / "tests").is_dir() or any(
            p.name.startswith("test_") or p.name.endswith("_test.py")
            for p in path.iterdir() if p.is_file()
        )

        return EntryPointsSummary(
            entry_scripts=entry_scripts,
            cli_commands=cli_commands,
            has_tests=has_tests,
        )

    def _resolve_target(
        self,
        target: Union[str, ProjectRecord, Path],
    ) -> Tuple[str, str, Optional[ProjectRecord]]:
        """Resolve name, path, and optional ProjectRecord from target."""
        if isinstance(target, ProjectRecord):
            return target.name, target.path, target

        if isinstance(target, Path):
            return target.name, str(target), None

        if isinstance(target, str):
            if self._project_registry and self._project_registry.has_project(target):
                record = self._project_registry.get_project(target)
                if record:
                    return record.name, record.path, record

            if self._workspace_manager:
                try:
                    resolved = self._workspace_manager.resolve_path(target, enforce_boundary=False)
                    if resolved.exists():
                        return resolved.name, str(resolved), None
                except Exception:
                    pass

            p_path = Path(target)
            return p_path.name, str(p_path), None

        raise GenovaOperatorError(f"Unsupported target type for inspection: {type(target)}")
