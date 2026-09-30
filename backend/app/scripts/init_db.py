"""Create the schema from the SQLAlchemy metadata.

⚠️ The canonical production path is the versioned SQL in ``database/migrations``
(which also installs RLS policies, triggers and indexes). This helper exists for
local development and for the test suite, where a throwaway SQLite database is
built from the same metadata.

Usage::

    python -m app.scripts.init_db          # create missing tables
    python -m app.scripts.init_db --drop   # ⚠️ drop everything first (dev only)
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import inspect

from app.config import settings
from app.database import engine
from app.models import Base
from app.models.competition import CompetitionSettings
from app.models.enums import CATEGORY_SEED


async def create_schema(drop: bool = False) -> list[str]:
    async with engine.begin() as conn:
        if drop:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        names = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
    return sorted(names)


async def ensure_baseline_rows() -> None:
    """Insert the singleton competition row and the default category list."""
    from sqlalchemy import select

    from app.database import session_scope
    from app.models.challenges import Category

    async with session_scope() as session:
        settings_row = await session.get(CompetitionSettings, 1)
        if settings_row is None:
            session.add(
                CompetitionSettings(
                    id=1,
                    name="WANO CTF",
                    tagline="Think. Hack. Capture. Defend.",
                    timezone=settings.ctf_timezone,
                )
            )
        existing = {
            slug
            for (slug,) in (await session.execute(select(Category.slug))).all()
        }
        for index, item in enumerate(CATEGORY_SEED):
            if item["slug"] in existing:
                continue
            session.add(
                Category(
                    slug=item["slug"],
                    name=item["name"],
                    icon=item["icon"],
                    description=item["description"],
                    display_order=index,
                )
            )


async def main() -> int:
    parser = argparse.ArgumentParser(description="Initialise the WANO CTF database schema.")
    parser.add_argument("--drop", action="store_true", help="drop existing tables first (dev only)")
    parser.add_argument("--no-seed", action="store_true", help="skip categories/competition rows")
    args = parser.parse_args()

    if args.drop and settings.is_production:
        print("Refusing to drop tables in production.", file=sys.stderr)
        return 2

    tables = await create_schema(drop=args.drop)
    print(f"Schema ready ({len(tables)} tables):")
    for name in tables:
        print(f"  - {name}")

    if not args.no_seed:
        await ensure_baseline_rows()
        print("Baseline rows ensured (competition_settings, categories).")

    await engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
