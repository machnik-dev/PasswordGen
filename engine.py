"""
engine.py — Password generation and strength scoring.
Uses Python's secrets module (CSPRNG). No Qt dependency.
"""

import secrets
import string


class PasswordEngine:
    LOWER   = string.ascii_lowercase
    UPPER   = string.ascii_uppercase
    DIGITS  = string.digits
    SPECIAL = "!@#$%^&*()-_=+[]{}|;:,.<>?"

    @staticmethod
    def generate(length, use_lower, use_upper, use_digits, use_special):
        pool, required = "", []
        for flag, charset in [
            (use_lower,   PasswordEngine.LOWER),
            (use_upper,   PasswordEngine.UPPER),
            (use_digits,  PasswordEngine.DIGITS),
            (use_special, PasswordEngine.SPECIAL),
        ]:
            if flag:
                pool += charset
                required.append(secrets.choice(charset))
        if not pool:
            return ""
        remaining = [secrets.choice(pool) for _ in range(length - len(required))]
        combined  = required + remaining
        secrets.SystemRandom().shuffle(combined)
        return "".join(combined)

    @staticmethod
    def strength(pw):
        """Returns (score 0–100, label str)."""
        if not pw:
            return 0, ""
        score = min(len(pw) * 2, 40)
        for cs in [PasswordEngine.LOWER, PasswordEngine.UPPER,
                   PasswordEngine.DIGITS, PasswordEngine.SPECIAL]:
            if any(c in cs for c in pw):
                score += 15
        score = min(score, 100)
        if score < 40:  return score, "Weak"
        if score < 65:  return score, "Fair"
        if score < 85:  return score, "Strong"
        return score, "Excellent"
