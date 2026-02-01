if you write file run then lint on this file with

```sh
make lint FILE=bot/...
```

and test with

```sh
make test FILE=bot/tests/...
```

When running any Python scripts, project tools, or tasks that require the project's dependencies/environment, ALWAYS use `uv run`. This ensures the command executes within the correct virtual environment.
For example:
- Running a script: `uv run python script.py`
- Running a module: `uv run python -m module_name`
- Running a tool: `uv run pytest` (unless using `make` which handles this)

When importing modules, use absolute imports instead of relative ones. For example, instead of `from bot.services.ytdlp import YtdlpDownloader`, use `from services.ytdlp import YtdlpDownloader`.

When managing tasks, use the `tasks` CLI.
- Create a new task: `tasks new "Task Title"`
- List open tasks: `tasks list`
- Edit a task: `tasks edit <timestamp>`
- Show a task: `tasks show <timestamp>`
- Clean closed tasks: `tasks clean`

Always write a plan in the `task.md` file created for the task and ask the user to approve it before implementing changes.
Do not remove the status and priority fields from the `task.md` file when updating it.

When checking types with `isinstance`, if the check fails, raise an appropriate exception (e.g., `ValueError` or `TypeError`) with a clear message instead of returning `None` or handling it silently, unless returning `None` is explicitly required by the logic.

Avoid using `try...except` blocks for control flow. Instead, use explicit checks (e.g., `isinstance`, `hasattr`, or boolean checks) to handle expected conditions. `try...except` should be reserved for truly exceptional circumstances or when interacting with external resources where failures are unpredictable.