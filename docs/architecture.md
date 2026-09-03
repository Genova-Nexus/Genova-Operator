# Architecture Overview — Genova Operator

Genova Operator is organized into modular layers designed to operate independently while providing unified operational interfaces.

## Philosophy: "Genova Nexus thinks, Genova Operator acts."

Genova Nexus serves as the high-level intelligent decision maker, while **Genova Operator** provides the practical capabilities required to inspect projects, execute commands, run experiments, monitor processes, manage automated jobs, and report structured results.

---

## Core Architecture (Day 2)

```text
                       ┌─────────────────────────┐
                       │     GENOVA NEXUS        │
                       └────────────┬────────────┘
                                    │ TaskRequest / TaskResult
                                    ▼
                       ┌─────────────────────────┐
                       │     GenovaOperator      │  (Central Orchestrator)
                       └──────┬───────────┬──────┘
                              │           │
                     ┌────────┴───┐   ┌───┴─────────────┐
                     │  EventBus  │   │  BaseComponent  │
                     └────────────┘   └─────────────────┘
```

### Core Components & Classes

1. **`GenovaOperator`** (`src/genova_operator/core/operator.py`):
   - Central control instance and orchestrator.
   - Manages component registration, lifecycle (`initialize()`, `shutdown()`), status monitoring, and task routing (`submit_task()`).

2. **Data Contracts** (`src/genova_operator/core/types.py`):
   - **`TaskRequest`**: Standard payload submitted from Genova Nexus (action, project name, parameters, options, metadata).
   - **`TaskResult`**: Standard payload returned to Genova Nexus (task ID, status, exit code, stdout, stderr, metrics, duration).
   - **`TaskState`**: Execution status enum (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`, `TIMEOUT`).
   - **`OperatorStatus`**: Operational state enum (`UNINITIALIZED`, `READY`, `BUSY`, `ERROR`, `SHUTDOWN`).
   - **`OperatorEvent`**: Data structure for internal events.

3. **`EventBus`** (`src/genova_operator/core/event_bus.py`):
   - Thread-safe publish-subscribe event bus supporting topic filtering and global subscribers.
   - Allows decoupled event monitoring by internal components and external observers.

4. **Interfaces & Protocols** (`src/genova_operator/core/interfaces.py`):
   - `BaseComponent`: Abstract lifecycle interface (`initialize()`, `shutdown()`, `get_status()`).
   - `BaseTaskRunner`: Interface for task execution engines.
   - `BaseProjectRegistry`: Interface for project discovery and lookup.

5. **Exceptions** (`src/genova_operator/core/exceptions.py`):
   - `GenovaOperatorError`: Base exception class.
   - `ComponentInitializationError`, `TaskExecutionError`, `ProjectNotFoundError`, `ConfigurationError`, `ComponentNotFoundError`.

---

## 60-Day Architecture Roadmap

1. **Phase 1: Foundation and Core Architecture** (Days 1–7)
   - Day 1: Project Foundation (Repository, Packaging, `.gitignore`)
   - Day 2: Core Architecture (`Operator Core`, Orchestrator, EventBus, Data Contracts)
   - Day 3: Configuration Manager (`Operator Config`)
   - Day 4: Workspace Manager
   - Day 5: Project Registry
   - Day 6: Project Discovery
   - Day 7: Foundation Validation
2. **Phase 2: Project Operations** (Days 8–14)
3. **Phase 3: Execution Engine** (Days 15–21)
4. **Phase 4: Monitoring and Observability** (Days 22–28)
5. **Phase 5: Git and Development Awareness** (Days 29–33)
6. **Phase 6: Automation** (Days 34–40)
7. **Phase 7: Pipelines and Research Operations** (Days 41–47)
8. **Phase 8: ML and AutoML Operations** (Days 48–52)
9. **Phase 9: Genova Nexus Integration** (Days 53–56)
10. **Phase 10: Production Validation and Release** (Days 57–60)
