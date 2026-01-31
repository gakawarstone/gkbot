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