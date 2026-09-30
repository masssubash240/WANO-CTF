"""Round 1 challenge dataset definitions for WANO CTF - Part 2."""

from app.models.enums import Difficulty

CHALLENGES_PART_2 = [
    # FORENSICS (3)
    {
        "title": "Magic Bytes",
        "slug": "magic-bytes",
        "category": "forensics",
        "difficulty": Difficulty.EASY,
        "points": 100,
        "flag": "WANO{png_h34d3r_89_50_4e_47}",
        "description": "An analyst retrieved an image whose first 8 header bytes were corrupted with zeroes. Restore the PNG magic header (89 50 4E 47 0D 0A 1A 0A) to view the image.",
        "hints": [
            {"text": "Open the damaged file in a hex editor like GHex or xxd.", "cost": 15},
            {"text": "Replace the first 8 bytes with: 89 50 4E 47 0D 0A 1A 0A", "cost": 30},
        ],
        "artifact": ("corrupt_artifact.png", "\x89PNG\r\n\x1a\nCorrupt-Recovery-Flag: WANO{png_h34d3r_89_50_4e_47}", "image/png"),
    },
    {
        "title": "Hidden In Plain Sight",
        "slug": "hidden-in-plain-sight",
        "category": "forensics",
        "difficulty": Difficulty.MEDIUM,
        "points": 150,
        "flag": "WANO{3x1f_m3t4d4t4_h1dd3n_fl4g}",
        "description": "Digital cameras store camera settings, GPS coordinates, and copyright info inside EXIF metadata tags. Inspect the provided image metadata to locate the flag.",
        "hints": [
            {"text": "Use exiftool or strings on the downloaded artifact.", "cost": 25},
            {"text": "Check the Comment or Artist tags in EXIF.", "cost": 40},
        ],
        "artifact": ("evidence.jpg", "JFIF Exif metadata\nArtist: WANO CTF\nComment: WANO{3x1f_m3t4d4t4_h1dd3n_fl4g}\n", "image/jpeg"),
    },
    {
        "title": "Corrupt Zip Recovery",
        "slug": "corrupt-zip-recovery",
        "category": "forensics",
        "difficulty": Difficulty.HARD,
        "points": 250,
        "flag": "WANO{z1p_c3ntr4l_d1r_r3p41r}",
        "description": "A suspect attempted to shred a ZIP archive by overwriting the end of central directory signature (50 4B 05 06). Repair the archive structure to extract flag.txt.",
        "hints": [
            {"text": "Look for the PK zip record headers (PK 03 04, PK 01 02, PK 05 06).", "cost": 40},
            {"text": "Use zip -FF or 7z to repair the damaged central directory.", "cost": 60},
        ],
    },
    # OSINT (2)
    {
        "title": "The Way Back",
        "slug": "the-way-back",
        "category": "osint",
        "difficulty": Difficulty.EASY,
        "points": 100,
        "flag": "WANO{w4yb4ck_m4ch1n3_n3v3r_f0rg3ts}",
        "description": "A rogue organisation deleted their public manifesto from their domain in January 2024. Use the Internet Archive Wayback Machine to retrieve the archived snapshot.",
        "hints": [
            {"text": "The web archive stores historic snapshots of websites over time.", "cost": 15},
            {"text": "Visit web.archive.org and inspect snapshots from 2024.", "cost": 25},
        ],
    },
    {
        "title": "Coordinate Strike",
        "slug": "coordinate-strike",
        "category": "osint",
        "difficulty": Difficulty.MEDIUM,
        "points": 150,
        "flag": "WANO{35_6762_n_139_6503_e_shibuya}",
        "description": "A leaked photo displays a distinctive pedestrian crossing with neon billboards and a Starbucks overlooking a massive intersection. Find the exact landmark name and its GPS coordinate.",
        "hints": [
            {"text": "Look closely at the pedestrian crossing geometry and Tokyo signs.", "cost": 25},
            {"text": "It is the famous Shibuya Scramble Crossing in Tokyo.", "cost": 40},
        ],
    },
    # LINUX (2)
    {
        "title": "SUID Hunting",
        "slug": "suid-hunting",
        "category": "linux",
        "difficulty": Difficulty.EASY,
        "points": 100,
        "flag": "WANO{su1d_f1nd_pr1v_3sc}",
        "description": "A misconfigured Linux host has an executable with the SetUID bit set (-rwsr-xr-x) owned by root. Locate this binary using find and escalate privileges.",
        "hints": [
            {"text": "The find command has a -perm parameter for permissions.", "cost": 15},
            {"text": "Run: find / -perm -4000 -type f 2>/dev/null", "cost": 30},
        ],
    },
    {
        "title": "Cron Misdirection",
        "slug": "cron-misdirection",
        "category": "linux",
        "difficulty": Difficulty.MEDIUM,
        "points": 200,
        "flag": "WANO{cr0n_w0rld_wr1t4bl3_scr1pt}",
        "description": "The root crontab runs a backup maintenance script every minute at /opt/backup/clean.sh. The script has world-writable permissions (777). Abuse it to capture /root/flag.txt.",
        "hints": [
            {"text": "Check files listed in /etc/crontab and /etc/cron.d/.", "cost": 25},
            {"text": "Since you can write to clean.sh, append a command to copy /root/flag.txt to /tmp.", "cost": 50},
        ],
    },
]
