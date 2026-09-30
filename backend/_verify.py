"""Runtime integrity check for the service layer (temporary)."""

import ast
import pathlib
import sys

problems = []

for path in sorted(pathlib.Path("app/services").glob("*.py")):
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        problems.append(f"SYNTAX {path}: {exc}")
        continue

    seen: dict[str, int] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in seen:
                problems.append(f"DUP    {path}: {node.name} (line {node.lineno})")
            seen[node.name] = node.lineno

sys.path.insert(0, ".")
for mod in [
    "audit",
    "teams",
    "challenges",
    "scoring",
    "scoreboard",
    "announcements",
    "files",
    "admin",
    "competition",
]:
    try:
        __import__(f"app.services.{mod}")
    except Exception as exc:
        problems.append(f"IMPORT app/services/{mod}.py: {type(exc).__name__}: {exc}")

print("\n".join(problems) if problems else "ALL CLEAN")
