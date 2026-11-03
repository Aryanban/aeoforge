"""Cloudflare XOR cipher deobfuscator and email extractor.
Ported and optimized from LeadForge (https://github.com/Aryanban/leadforge).
"""

import re
from typing import List, Set


def deobfuscate_cloudflare_email(cf_hex: str) -> str:
    """Decode a Cloudflare data-cfemail XOR encoded hex string.

    The first 2 hex characters represent the XOR key.
    Each subsequent 2 hex characters are XOR'd with the key to reveal the character.
    """
    if not cf_hex or len(cf_hex) < 4:
        return ""
    try:
        r = int(cf_hex[:2], 16)
        email_chars = []
        for n in range(2, len(cf_hex), 2):
            char_code = int(cf_hex[n:n + 2], 16) ^ r
            email_chars.append(chr(char_code))
        return "".join(email_chars)
    except Exception:
        return ""


def extract_obfuscated_emails(html_content: str) -> List[str]:
    """Extract and decode all Cloudflare and text-mutated emails from HTML."""
    found_emails: Set[str] = set()

    # 1. Match Cloudflare data-cfemail attributes
    cf_matches = re.findall(r'data-cfemail=["\']([a-fA-F0-9]+)["\']', html_content)
    for cf_hex in cf_matches:
        decoded = deobfuscate_cloudflare_email(cf_hex)
        if decoded and "@" in decoded and "." in decoded:
            found_emails.add(decoded.lower().strip())

    # 2. Match standard mailto: links
    mailto_matches = re.findall(r'href=["\']mailto:([^"\'\?]+)["\']', html_content, re.IGNORECASE)
    for mailto in mailto_matches:
        email = mailto.strip().lower()
        if "@" in email and "." in email:
            found_emails.add(email)

    # 3. Match text-mutated emails like user [at] domain [dot] com
    mutated = re.findall(
        r'([a-zA-Z0-9_.+-]+)\s*(?:\[at\]|\(at\)|@)\s*([a-zA-Z0-9-]+)\s*(?:\[dot\]|\(dot\)|\.)\s*([a-zA-Z]{2,10})',
        html_content,
        re.IGNORECASE
    )
    for user, domain, tld in mutated:
        found_emails.add(f"{user}@{domain}.{tld}".lower())

    return sorted(list(found_emails))
