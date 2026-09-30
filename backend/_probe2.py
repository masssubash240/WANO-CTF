"""Probe with error handling."""
import sys, traceback

with open("_probe_out.txt", "w") as f:
    f.write("Starting probe...\n")
    try:
        import importlib
        for mod in ["app.schemas.competition", "app.services.competition"]:
            try:
                m = importlib.import_module(mod)
                names = dir(m)
                targets = {"CompetitionState", "CompetitionPublic", "get_settings_row", "compute_state", "get_public_state"}
                found = [n for n in names if n in targets]
                f.write(f"{mod}: found={found}\n")
            except Exception as e:
                f.write(f"{mod}: ERROR: {e}\n")
                traceback.print_exc(file=f)
    except Exception as e:
        f.write(f"OUTER ERROR: {e}\n")
        traceback.print_exc(file=f)
    f.write("Done.\n")
