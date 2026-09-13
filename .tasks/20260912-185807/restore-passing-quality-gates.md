# Restore passing quality gates

- STATUS: OPEN
- PRIORITY: 2

## Problem

`make lint` currently fails. Ruff reports 453 findings. Mypy reports one test typing error, and Pyright reports that error plus the two existing GKFeed attribute errors. The unit suite passes 59 tests while skipping 13 provider and integration tests. The Serveo Go service has no tests, and `go vet` reports unreachable shutdown code.

## Plan

1. Finish the existing Piokok and Stories tasks that account for two Pyright errors.
2. Apply Ruff's safe fixes in reviewable batches, then fix the remaining correctness findings by category.
3. Narrow mypy's missing-import exemptions to packages that have no usable type information.
4. Fix the `MagicMock.__class__` assignment in `test_downstream_results.py` without suppressing either type checker.
5. Remove debugger calls from test helpers and make test doubles assert meaningful behavior when integration mode is off.
6. Add focused tests for the Python and Go runtime paths covered by the review tasks.
7. Fix the unreachable Serveo shutdown flow and run `go vet` for the service.
8. Keep `make lint`, `make test`, and Go checks in the project's automated verification path.

## Acceptance criteria

- `make lint` and `make test` pass.
- The Serveo Go service passes `go test` and `go vet`.
- Missing-import suppression is scoped and documented.
- Skipped tests state which external dependency they require.
