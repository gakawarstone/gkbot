# Bot API compatibility

The client is pinned to `aiogram==3.31.0` in `pyproject.toml`, `uv.lock`,
`requirements.txt`, and `requirements-dev.txt`. The local server in
`docker-compose.yml` is pinned to Bot API 10.3 using the multi-platform image
digest `sha256:779f6a18990d7df3b89b335e314bc3a92812530cfe08264824ac586225a6d6b3`.
The digest prevents the image from changing when its tag is republished.

## Confirmed API contract

The [aiogram 3.31.0 changelog](https://docs.aiogram.dev/en/latest/changelog.html)
and [Telegram Bot API 10.3 changelog](https://core.telegram.org/bots/api#august-24-2026)
confirm support for these interfaces. The installed wheel also exposes them:

- `InlineKeyboardButton(disabled=DisabledButton())` sends `"disabled": {}`.
  `disabled=True` is not the API contract. A disabled button needs no
  `callback_data`.
- `Bot.send_message_draft(..., can_stop=True, keep_on_stop=True)` sends draft
  stop controls. `Dispatcher.stopped_message_generation` receives
  `MessageGenerationStopped` updates with `chat` and `draft_id`.
- `Bot.send_rich_message(..., rich_message=InputRichMessage(...))` sends rich
  content.
- `ephemeral_message_parameters=EphemeralMessageParameters(...)` describes the
  recipient and callback relationship for ephemeral messages.
- `ChatMemberAdministrator` and `ChatAdministratorRights` require
  `can_send_welcome_messages` in administrator responses, including those
  requested by `/admins`.

This upgrade supplies library and server support. Application handlers retain
their existing behavior; enabling new features belongs to their own changes.

## Server verification and rollout order

On 2026-10-22, the existing `gkbot-api` container still referenced
`aiogram/telegram-bot-api:latest`, image ID
`sha256:5518232e8ede9b6de8dfc8a665a03104005732eb5d0ce33c5161ca6a361c8e77`.
An isolated invocation of that image's binary reported **Bot API 9.5**.
The pinned image's binary reported **Bot API 10.3** on linux/amd64.
No running production container was changed during verification.

Read the deployed image ID without reading its environment:

```bash
docker inspect --format '{{.Image}}' gkbot-api
```

Verify the pinned binary without credentials, networking, mounted data, or the
image entrypoint:

```bash
docker run --rm --network none --entrypoint /usr/local/bin/telegram-bot-api \
  aiogram/telegram-bot-api:10.3@sha256:779f6a18990d7df3b89b335e314bc3a92812530cfe08264824ac586225a6d6b3 \
  --version
```

An operator must update the server to this pinned image **before** rolling out
the new Python client or enabling Bot API 10.3 features. An old server can reject
new requests, and its administrator responses lack fields required by the new
client. Merging a Compose change does not update the running container.
Custom `API_SERVER_URL` deployments must meet the same Bot API 10.3 requirement.

After the server and bot rollout, verify polling, an existing delete callback,
HTML text, photo upload, AI chat, and `/admins` in a controlled Telegram chat.
Live Telegram smoke tests require deployment access and credentials and were
not performed for this change.

## Reproducing local checks

```bash
uv sync --locked
make test
make lint
docker compose -f services/bot-api/docker-compose.yml config --no-env-resolution --images
```

The clean starting commit `dfdecceb2e97824e924538bf7720c2547a7156a7` has
105 passing tests and 13 skipped integration tests. Its `make lint` stops at
391 existing Ruff findings. The upgrade does not clean up those unrelated
findings.

After the upgrade, `make test` reports **105 passed, 13 skipped**. The full `make lint`
output is byte-for-byte identical to the starting commit's output and stops at
the same 391 Ruff findings, before the other lint stages run.

To regenerate dependency files, use `uv lock`, `uv sync --locked`, `make lock`,
and `make lock-dev` in that order. Syncing first keeps the development freeze
consistent with `uv.lock`.
