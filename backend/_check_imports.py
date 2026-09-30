import importlib
import traceback

MODULES = [
    "app.models",
    "app.schemas",
    "app.services.audit",
    "app.services.teams",
    "app.services.challenges",
    "app.services.scoring",
    "app.services.scoreboard",
    "app.services.announcements",
    "app.services.files",
    "app.services.competition",
    "app.security.deps",
]

failed = False
for name in MODULES:
    try:
        importlib.import_module(name)
        print(f"OK   {name}")
    except Exception:
        failed = True
        print(f"FAIL {name}")
        traceback.print_exc()

print("RESULT:", "FAILURES" if failed else "ALL IMPORTS OK")
