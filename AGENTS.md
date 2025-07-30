# Agents

This file contains information about using various tools and commands in this project.

## Linting

To find linting errors in the codebase, you can use the `make lint` command. This command runs several linting tools including ruff, typos, mypy, and pyright to check for code quality issues, type errors, and spelling mistakes.

```bash
make lint
```

You can also specify a specific file or directory to lint:

```bash
make lint FILE=bot/core/bot.py
```