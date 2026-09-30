"""Round 1 challenge dataset definitions for WANO CTF - Part 3."""

from app.models.enums import Difficulty

CHALLENGES_PART_3 = [
    # REVERSE (2)
    {
        "title": "String Theory",
        "slug": "string-theory",
        "category": "reverse",
        "difficulty": Difficulty.EASY,
        "points": 100,
        "flag": "WANO{str1ngs_c0mm4nd_34sy_w1n}",
        "description": "An inexperienced programmer hardcoded the flag directly into the binary's .rodata section. Extract printable strings from the binary to recover the flag.",
        "hints": [
            {"text": "You do not need a full decompiler for plaintext string literals.", "cost": 15},
            {"text": "Run: strings binary_target | grep WANO", "cost": 25},
        ],
        "artifact": ("vault_checker.bin", "\x7fELF\x02\x01\x01\x00Target-Bin\x00Flag: WANO{str1ngs_c0mm4nd_34sy_w1n}\x00", "application/octet-stream"),
    },
    {
        "title": "Reverse the Gate",
        "slug": "reverse-the-gate",
        "category": "reverse",
        "difficulty": Difficulty.HARD,
        "points": 250,
        "flag": "WANO{x0r_k3y_d3c0d3_pr0}",
        "description": "Decompile the ELF x86-64 executable using Ghidra or IDA Pro. Function verify_serial() performs a byte-by-byte comparison after XORing input with constant 0x5A.",
        "hints": [
            {"text": "Locate the main() function and trace references to verify_serial().", "cost": 35},
            {"text": "The encrypted byte array is compared against your input XOR 0x5A.", "cost": 60},
        ],
    },
    # NETWORKING (2)
    {
        "title": "Packet Whispers",
        "slug": "packet-whispers",
        "category": "networking",
        "difficulty": Difficulty.EASY,
        "points": 100,
        "flag": "WANO{pcap_httq_g3t_fl4g_p4ck3t}",
        "description": "A network capture file contains unencrypted HTTP traffic. Open the .pcap in Wireshark and filter for GET requests containing the flag parameter.",
        "hints": [
            {"text": "Apply a display filter in Wireshark such as 'http.request.method == GET'.", "cost": 15},
            {"text": "Follow TCP stream on the HTTP session transmitting to port 80.", "cost": 25},
        ],
        "artifact": ("traffic_capture.pcap", "PCAP-DUMP-TRAFFIC\nGET /api/flag?token=WANO{pcap_httq_g3t_fl4g_p4ck3t} HTTP/1.1\nHost: ctf.wano.local\n", "application/vnd.tcpdump.pcap"),
    },
    {
        "title": "DNS Tunnel",
        "slug": "dns-tunnel",
        "category": "networking",
        "difficulty": Difficulty.MEDIUM,
        "points": 200,
        "flag": "WANO{dns_3xf1ltr4t10n_b4s332}",
        "description": "Malware exfiltrated classified data disguised as DNS subdomain queries (e.g. <hex>.corp.net). Extract the queries, concatenate the hex chunks, and decode the payload.",
        "hints": [
            {"text": "Filter Wireshark traffic with 'dns.qry.name'.", "cost": 30},
            {"text": "Tshark command: tshark -r dns.pcap -T fields -e dns.qry.name", "cost": 50},
        ],
    },
    # MISCELLANEOUS (3)
    {
        "title": "Welcome to WANO",
        "slug": "welcome-to-wano",
        "category": "misc",
        "difficulty": Difficulty.EASY,
        "points": 50,
        "flag": "WANO{w3lc0m3_t0_w4n0_ctf_2026}",
        "description": "Welcome Cadets to WANO CTF — Round 1! Submit this introductory flag to test your dashboard connection and score your first 50 points:\n\nWANO{w3lc0m3_t0_w4n0_ctf_2026}",
        "hints": [
            {"text": "Simply copy the flag format WANO{...} directly into the submit box.", "cost": 0},
        ],
    },
    {
        "title": "Invisible Ink",
        "slug": "invisible-ink",
        "category": "misc",
        "difficulty": Difficulty.EASY,
        "points": 100,
        "flag": "WANO{wh1t3sp4c3_c0d3_st3g}",
        "description": "This innocent text file appears to contain empty lines. However, inspect the trailing whitespace: combinations of tabs and spaces encode binary zeros and ones.",
        "hints": [
            {"text": "View whitespace characters using: cat -A filename or vim :set list", "cost": 15},
            {"text": "Convert spaces to 0 and tabs to 1, then convert to ASCII.", "cost": 30},
        ],
        "artifact": ("secret_ink.txt", "Hello Cadet!\n   \t  \t\n \t\t  \t \nFlag: WANO{wh1t3sp4c3_c0d3_st3g}\n", "text/plain"),
    },
    {
        "title": "Brainf***er",
        "slug": "brainf-ck",
        "category": "misc",
        "difficulty": Difficulty.MEDIUM,
        "points": 150,
        "flag": "WANO{3s0t3r1c_l4ngu4g3_m4st3r}",
        "description": "An intercepted script was written in an esoteric programming language containing only 8 characters: + - < > [ ] . ,. Execute the program to print the flag.",
        "hints": [
            {"text": "This is Brainfuck, created by Urban Müller in 1993.", "cost": 20},
            {"text": "Use an online Brainfuck interpreter or Python BF runner.", "cost": 35},
        ],
    },
]
