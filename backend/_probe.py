"""Temporary inspection helper (scratch)."""

import importlib

for mod in ["app.schemas.competition", "app.services.competition"]:
    m = importlib.import_module(mod)
    print(mod, "->", sorted(n for n in dir(m) if n in {"CompetitionState", "CompetitionPublic", "get_settings_row", "compute_state", "get_public_state"}))
