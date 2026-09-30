"""Round 1 challenge dataset definitions for WANO CTF."""

from app.models.enums import Difficulty

CHALLENGES_PART_1 = [
    # WEB (3)
    {
        "title": "Robots & Secrets",
        "slug": "robots-and-secrets",
        "category": "web",
        "difficulty": Difficulty.EASY,
        "points": 100,
        "flag": "WANO{r0b0ts_txt_disallow_all_secrets}",
        "description": "Standard web crawlers follow the Robots Exclusion Protocol. Check `/robots.txt` for disallowed directories and retrieve the hidden secret flag.",
        "hints": [
            {"text": "Search engine bots read a plaintext file located at the site root.", "cost": 15},
            {"text": "Check the Disallow directives inside /robots.txt.", "cost": 25},
        ],
        "artifact": ("robots.txt", "User-agent: *\nDisallow: /super-secret-admin-vault-2026/\n# Flag: WANO{r0b0ts_txt_disallow_all_secrets}\n", "text/plain"),
    },
    {
        "title": "Bypass The Gate",
        "slug": "bypass-the-gate",
        "category": "web",
        "difficulty": Difficulty.MEDIUM,
        "points": 150,
        "flag": "WANO{sql_1_3qu4ls_1_4uth_byp4ss}",
        "description": "An administrative login portal executes direct string concatenated SQL queries without parametrization: SELECT * FROM admins WHERE user = '{user}' AND pass = '{pass}'. Bypass the authentication check.",
        "hints": [
            {"text": "What happens if a single quote closes the query early?", "cost": 25},
            {"text": "Try the classic payload: ' OR 1=1 --", "cost": 50},
        ],
    },
    {
        "title": "Cookie Monster",
        "slug": "cookie-monster",
        "category": "web",
        "difficulty": Difficulty.HARD,
        "points": 250,
        "flag": "WANO{c00k13_t4mp3r1ng_pr1v_3sc}",
        "description": "The target website stores authorization state in an insecure base64-encoded session cookie session=eyJyb2xlIjogImd1ZXN0IiwgInVzZXIiOiAiY2FkZXQifQ==. Tamper with the cookie to claim the administrator privilege role.",
        "hints": [
            {"text": "Decode the base64 value of the session cookie to see its raw JSON.", "cost": 40},
            {"text": "Set the 'role' field to 'admin' and re-encode.", "cost": 60},
        ],
    },
    # CRYPTO (3)
    {
        "title": "Caesar's Whispers",
        "slug": "caesars-whispers",
        "category": "crypto",
        "difficulty": Difficulty.EASY,
        "points": 100,
        "flag": "WANO{shift_by_thirteen_rot_master}",
        "description": "Intercepted message from an ancient legion: JNAB{fuvsg_ol_guvegrra_ebg_znfgre}. Decrypt the ciphertext to obtain the flag.",
        "hints": [
            {"text": "This cipher was used by Julius Caesar, shifting letters by a fixed rotation.", "cost": 15},
            {"text": "Rotate by 13 positions (ROT13).", "cost": 25},
        ],
    },
    {
        "title": "Base of 64 Secrets",
        "slug": "base-of-64-secrets",
        "category": "crypto",
        "difficulty": Difficulty.EASY,
        "points": 100,
        "flag": "WANO{b4s3_64_1s_3nc0d1ng_n0t_crypt0}",
        "description": "A secret transmission was captured over an unencrypted radio frequency: V0FOT3tiNHMzXzY0XzFzXzNuYzBkMW5nX24wdF9jcnlwdDB9. Decode it to extract the hidden flag.",
        "hints": [
            {"text": "This is an encoding scheme using A-Z, a-z, 0-9, +, and /.", "cost": 15},
            {"text": "Run base64 -d in your terminal or use CyberChef.", "cost": 25},
        ],
    },
    {
        "title": "Broken XOR",
        "slug": "broken-xor",
        "category": "crypto",
        "difficulty": Difficulty.MEDIUM,
        "points": 200,
        "flag": "WANO{s1ngl3_byt3_x0r_cr4ck3d}",
        "description": "The flag was XORed with a single unknown byte key (0x00 - 0xFF). Ciphertext hex bytes: 17012e2f3b33712e277c13323934351338703213233274232b253d.",
        "hints": [
            {"text": "Every character in the flag was XORed with the exact same 1-byte value.", "cost": 30},
            {"text": "The first 5 bytes must XOR to 'WANO{'. Use that to deduce the key byte.", "cost": 45},
        ],
    },
]
