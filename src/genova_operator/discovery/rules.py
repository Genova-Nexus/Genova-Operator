"""Detection rules engine for Genova Operator Project Discovery.

Evaluates directories against markers, package definitions, version control,
and code structural layouts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from genova_operator.discovery.models import ProjectConfidence


def evaluate_directory(dir_path: Path) -> Tuple[ProjectConfidence, str, List[str], Dict[str, Any]]:
    """Evaluate a target directory and return detection results.

    Returns:
        Tuple of (ProjectConfidence, project_type, matched_rules, metadata)
    """
    if not dir_path.is_dir():
        return ProjectConfidence.NOT_A_PROJECT, "unknown", [], {}

    # Skip hidden/build folders
    if dir_path.name.startswith((".", "_")) or dir_path.name in ("dist", "build", "node_modules"):
        return ProjectConfidence.NOT_A_PROJECT, "unknown", [], {}

    matched_rules: List[str] = []
    metadata: Dict[str, Any] = {}
    score = 0.0

    # Rule 1: Explicit Genova Project Marker
    marker1 = dir_path / "genova_project.json"
    marker2 = dir_path / ".genova" / "project.json"
    if marker1.is_file() or marker2.is_file():
        matched_rules.append("explicit_genova_marker")
        score += 1.0
        m_file = marker1 if marker1.is_file() else marker2
        try:
            with open(m_file, "r", encoding="utf-8") as f:
                marker_data = json.load(f)
                metadata["marker_data"] = marker_data
                if "name" in marker_data:
                    metadata["custom_name"] = marker_data["name"]
                if "type" in marker_data:
                    metadata["custom_type"] = marker_data["type"]
        except Exception:
            pass

    # Rule 2: Python Package Definitions
    pyproject = dir_path / "pyproject.toml"
    setup_py = dir_path / "setup.py"
    setup_cfg = dir_path / "setup.cfg"
    req_txt = dir_path / "requirements.txt"

    if pyproject.is_file():
        matched_rules.append("pyproject_toml")
        score += 0.6
    if setup_py.is_file():
        matched_rules.append("setup_py")
        score += 0.5
    if setup_cfg.is_file():
        matched_rules.append("setup_cfg")
        score += 0.4
    if req_txt.is_file():
        matched_rules.append("requirements_txt")
        score += 0.4

    # Rule 3: Git Repository
    git_dir = dir_path / ".git"
    if git_dir.exists():
        matched_rules.append("git_repository")
        score += 0.3

    # Rule 4: Structural Layout
    src_dir = dir_path / "src"
    tests_dir = dir_path / "tests"
    main_py = dir_path / "main.py"
    app_py = dir_path / "app.py"

    if src_dir.is_dir():
        matched_rules.append("src_directory")
        score += 0.2
    if tests_dir.is_dir():
        matched_rules.append("tests_directory")
        score += 0.2
    if main_py.is_file():
        matched_rules.append("main_py_entry")
        metadata.setdefault("entry_points", {})["main"] = "main.py"
        score += 0.2
    if app_py.is_file():
        matched_rules.append("app_py_entry")
        metadata.setdefault("entry_points", {})["app"] = "app.py"
        score += 0.2

    # Determine Project Type
    project_type = metadata.get("custom_type", "python")
    if "requirements_txt" in matched_rules or "pyproject_toml" in matched_rules:
        if any(kw in str(dir_path).lower() for kw in ("ml", "ai", "fusion", "model", "data")):
            project_type = "ml_research"
        else:
            project_type = "python_library"

    # Classify Confidence
    if score >= 0.8:
        confidence = ProjectConfidence.HIGH
    elif score >= 0.4:
        confidence = ProjectConfidence.MEDIUM
    elif score > 0.0:
        confidence = ProjectConfidence.LOW
    else:
        confidence = ProjectConfidence.NOT_A_PROJECT

    return confidence, project_type, matched_rules, metadata
