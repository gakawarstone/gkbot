# Synchronize the command registry

- STATUS: OPEN
- PRIORITY: 2

## Problem

The command registry, Telegram default commands, literal handler registrations, and `/list` output disagree. `/start` and `/sub` are advertised without handlers, while `/admins` and `/set_tz` live outside the shared registry.

## Plan

1. Build one authoritative command definition used by registration, Telegram defaults, and `/list`.
2. Remove commands without handlers unless a handler is intentionally added.
3. Move literal command names into the shared definition.
4. Add a test that compares registered and advertised commands.

## Acceptance criteria

- `/list` contains only working user commands.
- Telegram default commands and handler registrations use the same names.
- No user command is defined only as an unrelated string literal.
- Command tests and static checks pass.

