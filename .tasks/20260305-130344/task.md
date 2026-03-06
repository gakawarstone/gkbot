# Add justfile with test command

Status: Completed
Priority: Normal

## Plan
1. Create a `justfile` in the project root.
2. Port the `test` command from `Makefile`.
3. Use `uv run` to execute `pytest` with the same configuration as in the `Makefile`.
4. Ensure the `test` command can accept an optional file or directory path as an argument.

## Task
- [x] Create `justfile`
- [x] Verify `just test` works
