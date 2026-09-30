"""Integrity sweep: duplicates, syntax, and import-time errors."""

import ast
import pathlib
import sys

root = pathlib.Path("app")
problems = 0

for path in sorted(root.rglob("*.py")):
    if "__pycache__" in str(path):
        continue
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as exc:
        print(f"SYNTAX  {path}:{exc.lineno}: {exc.msg}")
        problems += 1
        continue

    seen: dict[str, int] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in seen:
                print(f"DUPDEF  {path}:{node.lineno}: {node.name} (first at line {seen[node.name]})")
                problems += 1
            seen[node.name] = node.lineno
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", None) or ""
            for alias in node.names:
                name = f"{mod}.{alias.name}" if mod else alias.name
                line = src.splitlines()[node.lineno - 1]
                # A module-level import sitting after code is a strong smell.
                if node.col_offset == 0 and any(
                    isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                    and n.lineno < node.lineno
                    for n in tree.body
                ):
                    print(f"LATEIMP {path}:{node.lineno}: {name}")
                    problems += 1
                del line

print(f"\nTotal problems: {problems}")
sys.exit(1 if problems else 0)
