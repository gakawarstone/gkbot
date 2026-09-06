# Consolidate download callback handlers

- STATUS: OPEN
- PRIORITY: 3

## Problem

The YouTube, VK, Pornhub, and Porno365 download handlers repeat callback validation, status-message handling, downloader calls, media dispatch, and cleanup. Fixes must be copied across four implementations.

## Plan

1. Identify the stable shared workflow and source-specific hooks.
2. Introduce one typed base handler or helper for the shared workflow.
3. Keep URL construction and source-specific options in small adapters.
4. Preserve callback behavior while the callback-data migration remains a separate task.
5. Convert existing handler tests into shared contract tests.

## Acceptance criteria

- The four handlers use one implementation of the common download lifecycle.
- Source-specific behavior remains explicit.
- Existing callback formats remain compatible in this task.
- Shared and source-specific tests pass.

