"""Project Inspector models for Genova Operator.

Defines directory tree nodes, dependency summaries, repository inspection details,
environment inspection details, entry points summaries, and comprehensive ProjectInspectionReport objects.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DirectoryNode:
    """Represents a file or directory node in a project file tree.

    Attributes:
        name: File or directory basename.
        path: Relative path string from project root.
        is_dir: True if node is a directory.
        size_bytes: Size in bytes if a file.
        extension: File extension string if a file.
        children: Sub-nodes list if a directory.
    """
    name: str
    path: str
    is_dir: bool = False
    size_bytes: int = 0
    extension: str = ""
    children: List[DirectoryNode] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "is_dir": self.is_dir,
            "size_bytes": self.size_bytes,
            "extension": self.extension,
            "children": [child.to_dict() for child in self.children],
        }


@dataclass
class DirectoryTree:
    """Complete project directory structure tree.

    Attributes:
        root_name: Project root directory name.
        total_files: Count of total files scanned.
        total_directories: Count of total sub-directories scanned.
        total_size_bytes: Aggregate size of all files in bytes.
        root_node: Top-level DirectoryNode.
    """
    root_name: str
    total_files: int = 0
    total_directories: int = 0
    total_size_bytes: int = 0
    root_node: Optional[DirectoryNode] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_name": self.root_name,
            "total_files": self.total_files,
            "total_directories": self.total_directories,
            "total_size_bytes": self.total_size_bytes,
            "root_node": self.root_node.to_dict() if self.root_node else None,
        }


@dataclass
class DependencySummary:
    """Dependency information extracted from project package files.

    Attributes:
        dependencies: List of dependency names or specification strings.
        frameworks: Recognized key frameworks/libraries (e.g. 'torch', 'pytest', 'fastapi').
        package_files_found: List of package files detected (e.g. 'pyproject.toml', 'requirements.txt').
    """
    dependencies: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    package_files_found: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dependencies": self.dependencies,
            "frameworks": self.frameworks,
            "package_files_found": self.package_files_found,
            "count": len(self.dependencies),
        }


@dataclass
class RepositoryInspection:
    """Git repository inspection details.

    Attributes:
        is_git_repo: True if directory is a Git repository.
        branch: Active Git branch name.
        commit_hash: Latest commit SHA hash.
        remote_url: Git remote origin URL.
        is_dirty: True if uncommitted changes exist.
        changed_files_count: Count of modified/untracked files.
    """
    is_git_repo: bool = False
    branch: Optional[str] = None
    commit_hash: Optional[str] = None
    remote_url: Optional[str] = None
    is_dirty: bool = False
    changed_files_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_git_repo": self.is_git_repo,
            "branch": self.branch,
            "commit_hash": self.commit_hash,
            "remote_url": self.remote_url,
            "is_dirty": self.is_dirty,
            "changed_files_count": self.changed_files_count,
        }


@dataclass
class EnvironmentInspection:
    """Runtime environment inspection details.

    Attributes:
        environment_type: Detected environment type ('venv', 'conda', 'system').
        python_interpreter: Suggested/detected Python executable path.
        python_version: Detected Python version string.
        env_vars: Key environment variables configured.
    """
    environment_type: str = "system"
    python_interpreter: Optional[str] = None
    python_version: Optional[str] = None
    env_vars: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "environment_type": self.environment_type,
            "python_interpreter": self.python_interpreter,
            "python_version": self.python_version,
            "env_vars": self.env_vars,
        }


@dataclass
class EntryPointsSummary:
    """Runnable scripts and entry points detected in the project.

    Attributes:
        entry_scripts: Dict mapping alias to script path (e.g. {'main': 'main.py', 'train': 'scripts/train.py'}).
        cli_commands: List of detected CLI console commands.
        has_tests: True if test directory or test files detected.
    """
    entry_scripts: Dict[str, str] = field(default_factory=dict)
    cli_commands: List[str] = field(default_factory=list)
    has_tests: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_scripts": self.entry_scripts,
            "cli_commands": self.cli_commands,
            "has_tests": self.has_tests,
        }


@dataclass
class ProjectInspectionReport:
    """Comprehensive inspection report for a target project.

    Aggregates directory structure, configuration, dependencies, repository status,
    runtime environment, and entry points.
    """
    project_name: str
    project_path: str
    directory_tree: DirectoryTree
    dependencies: DependencySummary
    repository: RepositoryInspection
    environment: EnvironmentInspection
    entry_points: EntryPointsSummary
    metadata: Dict[str, Any] = field(default_factory=dict)
    inspected_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "project_path": self.project_path,
            "directory_tree": self.directory_tree.to_dict(),
            "dependencies": self.dependencies.to_dict(),
            "repository": self.repository.to_dict(),
            "environment": self.environment.to_dict(),
            "entry_points": self.entry_points.to_dict(),
            "metadata": self.metadata,
            "inspected_at": self.inspected_at,
        }
