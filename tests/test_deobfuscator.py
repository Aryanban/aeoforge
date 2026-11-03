"""Unit tests for Cloudflare XOR deobfuscator."""

from aeoforge.utils.deobfuscator import deobfuscate_cloudflare_email, extract_obfuscated_emails


def test_deobfuscate_cloudflare_email():
    # Cloudflare hex encoding for "test@example.com"
    # key = 0x58
    # 't' (0x74) ^ 0x58 = 0x2c
    # 'e' (0x65) ^ 0x58 = 0x3d
    # 's' (0x73) ^ 0x58 = 0x2b
    # 't' (0x74) ^ 0x58 = 0x2c
    # '@' (0x40) ^ 0x58 = 0x18
    # 'e' (0x65) ^ 0x58 = 0x3d
    # 'x' (0x78) ^ 0x58 = 0x20
    # 'a' (0x61) ^ 0x58 = 0x39
    # 'm' (0x6d) ^ 0x58 = 0x35
    # 'p' (0x70) ^ 0x58 = 0x28
    # 'l' (0x6c) ^ 0x58 = 0x34
    # 'e' (0x65) ^ 0x58 = 0x3d
    # '.' (0x2e) ^ 0x58 = 0x76
    # 'c' (0x63) ^ 0x58 = 0x3b
    # 'o' (0x6f) ^ 0x58 = 0x37
    # 'm' (0x6d) ^ 0x58 = 0x35
    hex_str = "582c3d2b2c183d20393528343d763b3735"
    assert deobfuscate_cloudflare_email(hex_str) == "test@example.com"
    assert deobfuscate_cloudflare_email("") == ""


def test_extract_obfuscated_emails_from_html():
    html = """
    <div>
        <span data-cfemail="582c3d2b2c183d20393528343d763b3735"></span>
        <a href="mailto:support@aeoforge.dev">Support</a>
        <p>Reach us at contact [at] aeoforge [dot] dev for help</p>
    </div>
    """
    emails = extract_obfuscated_emails(html)
    assert "test@example.com" in emails
    assert "support@aeoforge.dev" in emails
    assert "contact@aeoforge.dev" in emails
