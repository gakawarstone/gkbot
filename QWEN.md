if you write file run then lint on this file with

```sh
make lint FILE=bot/...
```

Rules:
- Do not use absolute package imports starting with "bot." inside repository code. Prefer relative imports within packages (e.g., from ..module import X) or top-level relative paths that align with current package structure.
