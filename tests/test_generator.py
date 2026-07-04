import string

from passman.generator import generate_password


class TestLength:
    def test_default_length(self):
        assert len(generate_password()) == 16

    def test_custom_length(self):
        assert len(generate_password(length=32)) == 32

    def test_length_smaller_than_required_classes(self):
        # With use_symbols=True and use_digits=True, 3 characters are
        # guaranteed (one letter, one symbol, one digit). Per the
        # docstring, requesting fewer than that yields a password
        # longer than requested rather than raising.
        password = generate_password(length=1, use_symbols=True, use_digits=True)
        assert len(password) == 3

    def test_length_exactly_equal_to_required_classes(self):
        password = generate_password(length=3, use_symbols=True, use_digits=True)
        assert len(password) == 3


class TestCharacterClasses:
    def test_letters_only(self):
        password = generate_password(length=20, use_symbols=False, use_digits=False)
        assert all(c in string.ascii_letters for c in password)

    def test_guarantees_letter_symbol_digit_when_all_enabled(self):
        # Run several times since placement/selection is randomized;
        # a single run isn't a strong enough guarantee check on its own,
        # but the guarantee should hold on every run.
        for _ in range(25):
            password = generate_password(length=16, use_symbols=True, use_digits=True)
            assert any(c in string.ascii_letters for c in password)
            assert any(c in string.punctuation for c in password)
            assert any(c in string.digits for c in password)

    def test_digits_enabled_without_symbols(self):
        password = generate_password(length=16, use_symbols=False, use_digits=True)
        assert all(c in string.ascii_letters + string.digits for c in password)
        assert any(c in string.digits for c in password)

    def test_symbols_enabled_without_digits(self):
        password = generate_password(length=16, use_symbols=True, use_digits=False)
        assert all(c in string.ascii_letters + string.punctuation for c in password)
        assert any(c in string.punctuation for c in password)


class TestRandomness:
    def test_two_calls_produce_different_passwords(self):
        # Not a formal randomness test -- just a smoke check that we're
        # not somehow returning a constant value.
        passwords = {generate_password(length=20) for _ in range(10)}
        assert len(passwords) == 10
