"""Execute complete seed for WANO CTF Round 1."""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select

from app.config import settings
from app.database import session_scope
from app.models.accounts import Profile
from app.models.challenges import Category, Challenge, ChallengeHint
from app.models.competition import CompetitionSettings, CompetitionStatus
from app.models.enums import Difficulty, TeamRole, UserRole
from app.models.files import ChallengeFile
from app.models.teams import Team, TeamMember
from app.security.flags import hash_flag
from app.security.passwords import hash_password
from app.seeds import ALL_ROUND_1_CHALLENGES


async def seed() -> None:
    async with session_scope() as session:
        comp = await session.get(CompetitionSettings, 1)
        if comp is None:
            comp = CompetitionSettings(
                id=1,
                name="WANO CTF — Round 1",
                tagline="Think. Hack. Capture. Defend.",
                status=CompetitionStatus.LIVE,
                submissions_enabled=True,
                registration_open=True,
                timezone=settings.ctf_timezone,
            )
            session.add(comp)
        else:
            comp.name = "WANO CTF — Round 1"
            comp.status = CompetitionStatus.LIVE
            comp.submissions_enabled = True
            comp.registration_open = True

        admin = (
            await session.execute(
                select(Profile).where(Profile.email == "admin@wano-fest.com")
            )
        ).scalar_one_or_none()
        if admin is None:
            admin = Profile(
                id=uuid.uuid4(),
                email="admin@wano-fest.com",
                full_name="Grand Marshal (Admin)",
                role=UserRole.ADMIN,
                email_verified=True,
                password_hash=hash_password("ChangeMe_Strong#2026"),
            )
            session.add(admin)

        player = (
            await session.execute(
                select(Profile).where(Profile.email == "operator@wano-fest.com")
            )
        ).scalar_one_or_none()
        if player is None:
            player = Profile(
                id=uuid.uuid4(),
                email="operator@wano-fest.com",
                full_name="Roronoa Zoro",
                role=UserRole.PARTICIPANT,
                college="Wano Academy",
                department="Cyber Defence",
                year="3rd Year",
                email_verified=True,
                password_hash=hash_password("Password123!"),
            )
            session.add(player)
            await session.flush()

            team = Team(
                id=uuid.uuid4(),
                name="StrawHat Pirates",
                name_normalized="strawhatpirates",
                team_code="STRAWH4T",
                college="Wano Academy",
                captain_id=player.id,
            )
            session.add(team)
            await session.flush()

            session.add(
                TeamMember(
                    team_id=team.id,
                    user_id=player.id,
                    role=TeamRole.CAPTAIN,
                )
            )

        categories = (await session.execute(select(Category))).scalars().all()
        cat_map = {c.slug: c.id for c in categories}
        from app.services.files import storage_root
        upload_dir = storage_root()
        upload_dir.mkdir(parents=True, exist_ok=True)

        from sqlalchemy.orm import selectinload

        for item in ALL_ROUND_1_CHALLENGES:
            cat_id = cat_map.get(item["category"]) or (categories[0].id if categories else None)

            existing_ch = (
                await session.execute(
                    select(Challenge)
                    .options(selectinload(Challenge.hints), selectinload(Challenge.files))
                    .where(Challenge.slug == item["slug"])
                )
            ).scalar_one_or_none()

            if existing_ch is None:
                ch = Challenge(
                    title=item["title"],
                    slug=item["slug"],
                    category_id=cat_id,
                    difficulty=item["difficulty"],
                    points=item["points"],
                    flag_hash=hash_flag(item["flag"]),
                    description=item["description"],
                    visible=True,
                )
                session.add(ch)
                await session.flush()
                hints_present = False
                files_present = False
            else:
                ch = existing_ch
                ch.title = item["title"]
                ch.difficulty = item["difficulty"]
                ch.points = item["points"]
                ch.description = item["description"]
                ch.flag_hash = hash_flag(item["flag"])
                ch.visible = True
                if cat_id:
                    ch.category_id = cat_id
                hints_present = bool(ch.hints)
                files_present = bool(ch.files)

            if "hints" in item and not hints_present:
                for idx, h in enumerate(item["hints"]):
                    session.add(
                        ChallengeHint(
                            challenge_id=ch.id,
                            text=h["text"],
                            cost=h["cost"],
                            display_order=idx + 1,
                            is_visible=True,
                        )
                    )

            if "artifact" in item and not files_present:
                fname, content, mtype = item["artifact"]
                disk_path = upload_dir / f"{ch.slug}_{fname}"
                disk_path.write_text(content, encoding="utf-8")

                file_rec = ChallengeFile(
                    challenge_id=ch.id,
                    filename=fname,
                    label=fname,
                    storage_path=str(disk_path),
                    size_bytes=len(content.encode("utf-8")),
                    mime_type=mtype,
                    sha256="mock_hash",
                )
                session.add(file_rec)

        await session.commit()
        print("Successfully seeded all 20 WANO CTF Round 1 challenges!")


if __name__ == "__main__":
    asyncio.run(seed())
