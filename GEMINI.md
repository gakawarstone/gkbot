if you write file run then lint on this file with

```sh
make lint FILE=bot/...
```

and test with

```sh
make test FILE=bot/tests/...
```

When running scripts or tasks, use `uv run`. For example:
```sh
uv run python script.py
```

When importing modules, use absolute imports instead of relative ones. For example, instead of `from bot.services.ytdlp import YtdlpDownloader`, use `from services.ytdlp import YtdlpDownloader`.

When managing tasks, use the `tasks` CLI.
- Create a new task: `tasks new "Task Title"`
- List open tasks: `tasks list`
- Edit a task: `tasks edit <timestamp>`
- Show a task: `tasks show <timestamp>`
- Clean closed tasks: `tasks clean`

Always write a plan in the `task.md` file created for the task and ask the user to approve it before implementing changes.