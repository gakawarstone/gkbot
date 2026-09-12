# Secure the yt-dlp supervisor upload endpoint

- STATUS: OPEN
- PRIORITY: 1

## Problem

`services/ytdlp_workers_supervisor/main.go` passes the request-controlled `id` to `filepath.Join(uploadPath, id, filename)`. Values such as `../tmp` can escape `/files`, and `os.Create` overwrites an existing file. The endpoint has no authentication, accepts uploads without a size limit, and Compose publishes it on host port 8092.

## Plan

1. Define the allowed format for upload IDs and reject path separators, traversal components, and empty values.
2. Resolve the destination path and verify that it remains below `/files` before opening a file.
3. Create the per-task directory explicitly and prevent overwriting an existing destination.
4. Add an upload size limit and require authentication or bind the service to a trusted network only.
5. Add Go tests for valid uploads, traversal attempts, oversized bodies, and duplicate filenames.

## Acceptance criteria

- No request field can make the service write outside `/files`.
- An upload cannot silently overwrite an existing file.
- Oversized and unauthenticated uploads receive an error response.
- Focused tests cover the rejected inputs and a successful upload.

