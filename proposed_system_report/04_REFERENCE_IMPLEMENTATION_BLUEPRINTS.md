# Volume 4 — Reference Implementation Blueprints

## Service Blueprint Modules
## Module: `session_manager`
### Directory Layout
```text
src/wyrdforge/services/session_manager.py
src/wyrdforge/models/session_manager_models.py
tests/session_manager/test_session_manager.py
```
### Minimal API Skeleton
```python
class Service:
    def __init__(self, config: dict):
        self.config = config

    async def run(self, request: dict) -> dict:
        # validate -> execute -> record telemetry -> return
        return {"ok": True, "service": self.__class__.__name__}
```
### Reliability Patterns
- Circuit breaker around upstream model and vector dependencies.
- Idempotency keys for mutation pathways.
- Structured errors with typed remediation hints.

## Module: `prompt_builder`
### Directory Layout
```text
src/wyrdforge/services/prompt_builder.py
src/wyrdforge/models/prompt_builder_models.py
tests/prompt_builder/test_prompt_builder.py
```
### Minimal API Skeleton
```python
class Service:
    def __init__(self, config: dict):
        self.config = config

    async def run(self, request: dict) -> dict:
        # validate -> execute -> record telemetry -> return
        return {"ok": True, "service": self.__class__.__name__}
```
### Reliability Patterns
- Circuit breaker around upstream model and vector dependencies.
- Idempotency keys for mutation pathways.
- Structured errors with typed remediation hints.

## Module: `router_policy`
### Directory Layout
```text
src/wyrdforge/services/router_policy.py
src/wyrdforge/models/router_policy_models.py
tests/router_policy/test_router_policy.py
```
### Minimal API Skeleton
```python
class Service:
    def __init__(self, config: dict):
        self.config = config

    async def run(self, request: dict) -> dict:
        # validate -> execute -> record telemetry -> return
        return {"ok": True, "service": self.__class__.__name__}
```
### Reliability Patterns
- Circuit breaker around upstream model and vector dependencies.
- Idempotency keys for mutation pathways.
- Structured errors with typed remediation hints.

## Module: `memory_store`
### Directory Layout
```text
src/wyrdforge/services/memory_store.py
src/wyrdforge/models/memory_store_models.py
tests/memory_store/test_memory_store.py
```
### Minimal API Skeleton
```python
class Service:
    def __init__(self, config: dict):
        self.config = config

    async def run(self, request: dict) -> dict:
        # validate -> execute -> record telemetry -> return
        return {"ok": True, "service": self.__class__.__name__}
```
### Reliability Patterns
- Circuit breaker around upstream model and vector dependencies.
- Idempotency keys for mutation pathways.
- Structured errors with typed remediation hints.

## Module: `micro_rag`
### Directory Layout
```text
src/wyrdforge/services/micro_rag.py
src/wyrdforge/models/micro_rag_models.py
tests/micro_rag/test_micro_rag.py
```
### Minimal API Skeleton
```python
class Service:
    def __init__(self, config: dict):
        self.config = config

    async def run(self, request: dict) -> dict:
        # validate -> execute -> record telemetry -> return
        return {"ok": True, "service": self.__class__.__name__}
```
### Reliability Patterns
- Circuit breaker around upstream model and vector dependencies.
- Idempotency keys for mutation pathways.
- Structured errors with typed remediation hints.

## Module: `truth_calibrator`
### Directory Layout
```text
src/wyrdforge/services/truth_calibrator.py
src/wyrdforge/models/truth_calibrator_models.py
tests/truth_calibrator/test_truth_calibrator.py
```
### Minimal API Skeleton
```python
class Service:
    def __init__(self, config: dict):
        self.config = config

    async def run(self, request: dict) -> dict:
        # validate -> execute -> record telemetry -> return
        return {"ok": True, "service": self.__class__.__name__}
```
### Reliability Patterns
- Circuit breaker around upstream model and vector dependencies.
- Idempotency keys for mutation pathways.
- Structured errors with typed remediation hints.

## Module: `bond_graph`
### Directory Layout
```text
src/wyrdforge/services/bond_graph.py
src/wyrdforge/models/bond_graph_models.py
tests/bond_graph/test_bond_graph.py
```
### Minimal API Skeleton
```python
class Service:
    def __init__(self, config: dict):
        self.config = config

    async def run(self, request: dict) -> dict:
        # validate -> execute -> record telemetry -> return
        return {"ok": True, "service": self.__class__.__name__}
```
### Reliability Patterns
- Circuit breaker around upstream model and vector dependencies.
- Idempotency keys for mutation pathways.
- Structured errors with typed remediation hints.

## Module: `event_ledger`
### Directory Layout
```text
src/wyrdforge/services/event_ledger.py
src/wyrdforge/models/event_ledger_models.py
tests/event_ledger/test_event_ledger.py
```
### Minimal API Skeleton
```python
class Service:
    def __init__(self, config: dict):
        self.config = config

    async def run(self, request: dict) -> dict:
        # validate -> execute -> record telemetry -> return
        return {"ok": True, "service": self.__class__.__name__}
```
### Reliability Patterns
- Circuit breaker around upstream model and vector dependencies.
- Idempotency keys for mutation pathways.
- Structured errors with typed remediation hints.

## Module: `eval_harness`
### Directory Layout
```text
src/wyrdforge/services/eval_harness.py
src/wyrdforge/models/eval_harness_models.py
tests/eval_harness/test_eval_harness.py
```
### Minimal API Skeleton
```python
class Service:
    def __init__(self, config: dict):
        self.config = config

    async def run(self, request: dict) -> dict:
        # validate -> execute -> record telemetry -> return
        return {"ok": True, "service": self.__class__.__name__}
```
### Reliability Patterns
- Circuit breaker around upstream model and vector dependencies.
- Idempotency keys for mutation pathways.
- Structured errors with typed remediation hints.

## Module: `safety_guard`
### Directory Layout
```text
src/wyrdforge/services/safety_guard.py
src/wyrdforge/models/safety_guard_models.py
tests/safety_guard/test_safety_guard.py
```
### Minimal API Skeleton
```python
class Service:
    def __init__(self, config: dict):
        self.config = config

    async def run(self, request: dict) -> dict:
        # validate -> execute -> record telemetry -> return
        return {"ok": True, "service": self.__class__.__name__}
```
### Reliability Patterns
- Circuit breaker around upstream model and vector dependencies.
- Idempotency keys for mutation pathways.
- Structured errors with typed remediation hints.
