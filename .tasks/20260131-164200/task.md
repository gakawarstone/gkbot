# Resolve TODO/FIXME comments across the codebase

- STATUS: OPEN
- PRIORITY: 4

## Plan
1.  **Analyze**:
    -   Scan the codebase for `TODO` and `FIXME` markers.
    -   Review the `review.md` list of specific technical debt items.
2.  **Execute**:
    -   **Phase 1 (Easy Fixes)**: Resolve minor formatting or obvious logic FIXMEs (e.g., `str` instead of `int`).
    -   **Phase 2 (Deprecations)**: Address deprecated handlers like `ask.py` (consider removing or updating if replacement exists).
    -   **Phase 3 (Complex)**: For items requiring significant architectural changes or missing features (e.g., "TTS Provider"), comment with a more detailed explanation or create a specific new Task for it if it cannot be done quickly.
3.  **Verify**:
    -   Re-scan to ensure the count of TODO/FIXME has decreased.
    -   Run tests to ensure refactoring didn't break functionality.