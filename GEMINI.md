if you write file run then lint on this file with

```sh
make lint FILE=bot/...
```

When importing modules, use absolute imports instead of relative ones. For example, instead of `from bot.services.ytdlp import YtdlpDownloader`, use `from services.ytdlp import YtdlpDownloader`.