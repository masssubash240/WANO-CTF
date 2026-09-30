"""Seed development database with admin, participant, team, and sample challenges."""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select

from app.database import session_scope
from app.models.accounts import Profile
from app.models.challenges import Category, Challenge
from app.models.enums import Difficulty, TeamRole, UserRole
from app.models.teams import Team, TeamMember
from app.security.flags import hash_flag
from app.security.passwords import hash_password


async def seed() -> None:
    async with session_scope() as session:
        # Check if already seeded
        admin_exists = (
            await session.execute(
                select(Profile).where(Profile.email == "admin@wano-fest.com")
            )
        ).scalar_one_or_none()

        from app.models.competition import CompetitionSettings
        from app.models.enums import CompetitionStatus

        comp = await session.get(CompetitionSettings, 1)
        if comp:
            comp.status = CompetitionStatus.LIVE
            comp.submissions_enabled = True

        if admin_exists:
            await session.commit()
            print("Dev database already has seed data. Competition marked LIVE.")
            return

        # 1. Admin Profile
        admin = Profile(
            id=uuid.uuid4(),
            email="admin@wano-fest.com",
            full_name="Grand Marshal (Admin)",
            role=UserRole.ADMIN,
            email_verified=True,
            password_hash=hash_password("ChangeMe_Strong#2026"),
        )
        session.add(admin)

        # 2. Player Profile
        player = Profile(
            id=uuid.uuid4(),
            email="operator@wano-fest.com",
            full_name="Neo Anderson",
            role=UserRole.PARTICIPANT,
            college="Cyber University",
            department="Computer Science",
            year="3rd Year",
            email_verified=True,
            password_hash=hash_password("Password123!"),
        )
        session.add(player)
        await session.flush()

        # 3. Player Team
        team = Team(
            id=uuid.uuid4(),
            name="ZeroCool",
            name_normalized="zerocool",
            team_code="ZER0C00L",
            captain_id=player.id,
        )
        session.add(team)
        await session.flush()

        membership = TeamMember(
            team_id=team.id,
            user_id=player.id,
            role=TeamRole.CAPTAIN,
        )
        session.add(membership)

        # 4. Fetch Categories
        categories = (await session.execute(select(Category))).scalars().all()
        cat_map = {c.slug: c.id for c in categories}

        # 5. Create Sample Challenges
        sample_challenges = [
            {
                "title": "Welcome to WANO",
                "slug": "welcome-to-wano",
                "category": "misc",
                "difficulty": Difficulty.EASY,
                "points": 50,
                "flag": "WANO{w3lc0m3_t0_w4n0_ctf_2026}",
                "description": "Welcome to the WANO Capture The Flag competition! To get started, submit your first flag right here:\n\n`WANO{w3lc0m3_t0_w4n0_ctf_2026}`",
            },
            {
                "title": "Robots & Secrets",
                "slug": "robots-and-secrets",
                "category": "web",
                "difficulty": Difficulty.EASY,
                "points": 100,
                "flag": "WANO{r0b0ts_txt_disallow_all_secrets}",
                "description": "Search engines love crawling websites, but webmasters use a specific text file at the website root to tell spiders where NOT to go. Can you uncover what is hidden in `/robots.txt`?",
            },
            {
                "title": "Caesar's Whispers",
                "slug": "caesars-whispers",
                "category": "crypto",
                "difficulty": Difficulty.EASY,
                "points": 100,
                "flag": "WANO{shift_by_thirteen_rot_master}",
                "description": "We intercepted this encrypted ciphertext: `JNAB{fuvsg_ol_guvegrra_ebg_znfgre}`. Decrypt the message to find the flag.",
            },
            {
                "title": "Magic Bytes",
                "slug": "magic-bytes",
                "category": "forensics",
                "difficulty": Difficulty.MEDIUM,
                "points": 150,
                "flag": "WANO{png_h34d3r_89_50_4e_47}",
                "description": "A corrupt image file has its header bytes zeroed out. Repair the standard PNG signature (`89 50 4E 47 0D 0A 1A 0A`) to view the image contents.",
            },
            {
                "title": "Reverse the Gate",
                "slug": "reverse-the-gate",
                "category": "reverse",
                "difficulty": Difficulty.HARD,
                "points": 250,
                "flag": "WANO{x0r_k3y_d3c0d3_pr0}",
                "description": "Decompile the provided binary and examine the password checking function `check_flag()`. It performs an XOR operation against the hardcoded key `0x5A`.",
            },
        ]

        for chal in sample_challenges:
            cat_id = cat_map.get(chal["category"])
            if not cat_id and categories:
                cat_id = categories[0].id
            if cat_id:
                ch = Challenge(
                    title=chal["title"],
                    slug=chal["slug"],
                    category_id=cat_id,
                    difficulty=chal["difficulty"],
                    points=chal["points"],
                    flag_hash=hash_flag(chal["flag"]),
                    description=chal["description"],
                    visible=True,
                )
                session.add(ch)

        await session.commit()
        print("Dev database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
