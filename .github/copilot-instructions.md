# Copilot Editing Rules for NovaForge

Follow these rules for every suggestion and code edit:

1. Change only what the user explicitly asks for.
2. Do not modify unrelated files, functions, routes, variables, IDs, classes, or styling.
3. Preserve existing behavior unless the request explicitly says to remove or replace it.
4. Keep diffs minimal. Prefer targeted line edits over large rewrites.
5. Do not refactor, rename, reorder, or reformat unrelated code.
6. If the request is ambiguous, ask for clarification before broad changes.
7. For backend edits, keep existing API contracts and response shapes unchanged unless explicitly requested.
8. For frontend edits, keep existing event handlers and feature flows working.
9. Avoid destructive actions (mass deletion, replacing full files) unless user asks for full redesign/rewrite.
10. In your response, briefly list exactly what was changed and what was intentionally left untouched.

Definition of done:
- Requested change works.
- Existing unrelated features remain intact.
- No incidental regressions introduced.
