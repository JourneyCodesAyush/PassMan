import secrets
import string

__all__ = ["generate_password"]


def generate_password(
    length: int = 16, use_symbols: bool = True, use_digits: bool = True
) -> str:
    """Generate a cryptographically random password.

    Uses `secrets.choice()` for character selection, never the
    non-cryptographic `random` module. At least one character from
    each enabled class (letters, digits, symbols) is guaranteed to
    appear, with final positions shuffled via `secrets.SystemRandom()`
    so the guaranteed characters aren't predictably placed.

    Length is not validated here — callers are responsible for
    enforcing a sane minimum (passman's REPL enforces 8). Note that
    `length` must be at least the number of enabled character classes
    (up to 3, when both `use_symbols` and `use_digits` are `True`) or
    the returned password will be longer than requested.

    Args:
        length: Desired password length. Defaults to 16.
        use_symbols: Include punctuation characters. Defaults to True.
        use_digits: Include digit characters. Defaults to True.

    Returns:
        A randomly generated password string.
    """
    required = [secrets.choice(string.ascii_letters)]
    pool = string.ascii_letters

    if use_symbols:
        required.append(secrets.choice(string.punctuation))
        pool += string.punctuation
    if use_digits:
        required.append(secrets.choice(string.digits))
        pool += string.digits

    remaining = [secrets.choice(pool) for _ in range(length - len(required))]

    password_chars = required + remaining

    secrets.SystemRandom().shuffle(password_chars)

    return "".join(password_chars)
