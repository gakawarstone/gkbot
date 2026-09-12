# Decide how to replace the handler context manager

- STATUS: OPEN
- PRIORITY: 2

## Problem

The handler context manager derives field names through `varname` stack inspection and validates values with exact runtime type identity. Parameterized types such as `list[str]` fail and require raw-type workarounds.

## Plan

1. Inventory every context class and its stored value types.
2. Compare explicit field keys, dataclass serialization, typed mappings, and direct aiogram FSM data access.
3. Provide a migration plan that removes stack-frame dependence and supports parameterized containers.
4. Describe compatibility risks for in-progress FSM sessions and existing tests.
5. Stop and ask the task owner to approve the replacement design before implementation.

## Acceptance criteria

- The proposal covers every current context consumer.
- The chosen design has explicit keys and a defined runtime validation policy.
- The owner has approved the design before production code changes begin.

