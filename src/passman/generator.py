import secrets
import string


def generate_password(
    length: int = 16, use_symbols: bool = True, use_digits: bool = True
) -> str:

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
