"""Consolidated 20 official Round 1 challenges for WANO CTF."""

from app.seeds.challenges_data_part1 import CHALLENGES_PART_1
from app.seeds.challenges_data_part2 import CHALLENGES_PART_2
from app.seeds.challenges_data_part3 import CHALLENGES_PART_3

ALL_ROUND_1_CHALLENGES = [
    *CHALLENGES_PART_1,
    *CHALLENGES_PART_2,
    *CHALLENGES_PART_3,
]

assert len(ALL_ROUND_1_CHALLENGES) == 20, f"Expected 20 challenges, got {len(ALL_ROUND_1_CHALLENGES)}"
