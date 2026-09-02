# Genova Operator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-v0.1.0--dev-orange.svg)](https://github.com/Genova-Nexus/Genova-Operator)

**Genova Operator** is an open-source Python library designed to serve as the operational and automation layer for the **Genova Nexus** ecosystem.

> *"Genova Nexus thinks, Genova Operator acts."*

---

## 🎯 Overview & Purpose

Genova Nexus acts as the intelligent decision-making layer that understands user intents, plans complex research and development tasks, and determines what operations should occur. **Genova Operator** acts as the execution engine that turns those decisions into reliable actions on real software projects, scripts, machine learning workloads, pipelines, and research environments.

By decoupling intelligence from operational execution, Genova Operator allows Genova Nexus to manage diverse projects (such as `GeneFusionAI`, `Clarify`, and future ecosystem additions) through a unified, clean operational interface.

---

## 🏗️ Repository & Package Structure

```text
Genova Operator/
├── src/
│   └── genova_operator/
│       ├── __init__.py
│       ├── __version__.py
│       ├── py.typed
│       └── core/
│           └── __init__.py
├── tests/
│   ├── __init__.py
│   └── test_version.py
├── docs/
│   ├── index.md
│   ├── architecture.md
│   ├── setup_guide.md
│   └── nexus_relationship.md
├── pyproject.toml
├── LICENSE
├── README.md
├── planning_phase.txt
└── Idea.txt
```

---

## 🔄 Relationship: Genova Nexus & Genova Operator

```text
               ┌───────────────────────┐
               │     GENOVA NEXUS      │  (Intelligence & Decision Layer)
               └───────────┬───────────┘
                           │ Task Submission & Strategy
                           ▼
               ┌───────────────────────┐
               │    GENOVA OPERATOR    │  (Execution & Automation Layer)
               └───────────┬───────────┘
                           │ Inspection, Execution & Monitoring
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
   GeneFusionAI         Clarify       Future Projects
```

- **Genova Nexus**: Formulates goals, breaks down problems, analyzes context, and submits structured tasks.
- **Genova Operator**: Discovers projects, inspects local environments, executes commands/scripts, monitors processes and system resources, manages logs/events, automates jobs, and returns structured result objects.

---

## 🚀 Quick Start & Development Setup

### Installation (Development Mode)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Genova-Nexus/Genova-Operator.git
   cd Genova-Operator
   ```

2. **Set up virtual environment:**
   ```bash
   python -m venv _env
   # On Windows:
   _env\Scripts\activate
   # On Linux/macOS:
   source _env/bin/activate
   ```

3. **Install editable package with dev dependencies:**
   ```bash
   pip install -e .[dev]
   ```

### Running Tests

To run the test suite:
```bash
pytest
```

---

## 📌 Versioning Strategy

Genova Operator follows **Semantic Versioning** (`MAJOR.MINOR.PATCH`).
- Current development target: `v0.1.0-dev`
- Release target: `Genova Operator v0.1.0` (following 60-Day execution roadmap)

---

## 📄 License

Distributed under the MIT License. See [`LICENSE`](file:///e:/GenovaNexus/Genova%20Operator/LICENSE) for details.
