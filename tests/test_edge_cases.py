from logic_utils import check_guess, get_range_for_difficulty, parse_guess

# parse_guess(raw, low, high) returns (ok, value, error).
# Normal difficulty is 1-100, so that is the range these tests use.

# --- Edge case 1: out-of-range values ---


def test_negative_number_is_rejected():
    # "-7" used to be accepted: it burned an attempt and got a useless hint,
    # because nothing compared the guess to the difficulty's range.
    ok, value, error = parse_guess("-7", 1, 100)
    assert ok is False
    assert value is None
    assert error == "Enter a whole number between 1 and 100."


def test_zero_is_rejected():
    ok, value, _ = parse_guess("0", 1, 100)
    assert ok is False
    assert value is None


def test_number_above_the_range_is_rejected():
    ok, value, _ = parse_guess("101", 1, 100)
    assert ok is False
    assert value is None


def test_error_message_names_the_real_bounds():
    # Easy is 1-20, so the message must not say 100.
    low, high = get_range_for_difficulty("Easy")
    _, _, error = parse_guess("57", low, high)
    assert error == "Enter a whole number between 1 and 20."


# --- Edge case 2: decimals ---


def test_decimal_is_rejected():
    # int(float("50.9")) used to be 50, so 50.9 could WIN against a secret
    # of 50 and the history logged a number the player never typed.
    ok, value, error = parse_guess("50.9", 1, 100)
    assert ok is False
    assert value is None
    assert error == "Whole numbers only - no decimals or symbols."


def test_tiny_decimal_is_rejected():
    ok, value, _ = parse_guess("0.0000001", 1, 100)
    assert ok is False
    assert value is None


# --- Edge case 3: extremely large values ---


def test_huge_number_is_rejected():
    ok, value, _ = parse_guess("9" * 21, 1, 100)
    assert ok is False
    assert value is None


def test_very_long_number_is_not_called_not_a_number():
    # Python 3.11+ caps int() conversion at 4300 digits, so the old bare
    # except reported "That is not a number." about a valid number.
    ok, _, error = parse_guess("9" * 5000, 1, 100)
    assert ok is False
    assert "not a number" not in error.lower()


def test_check_guess_compares_big_numbers_as_numbers():
    # The old code compared them as text, where "9" > "10".
    outcome, _ = check_guess(10 ** 30, 50)
    assert outcome == "Too High"


# --- Numbers that look valid but are not ---


def test_scientific_notation_is_rejected():
    # The old parser branched on whether the text held a ".", so "1e3" was
    # rejected while "1.5e3" quietly became 1500.
    ok, value, _ = parse_guess("1e3", 1, 100)
    assert ok is False
    assert value is None


def test_hex_is_rejected():
    ok, value, _ = parse_guess("0x10", 1, 100)
    assert ok is False
    assert value is None


# --- Junk input should be turned away, not crash ---


def test_empty_input_is_rejected():
    ok, value, error = parse_guess("", 1, 100)
    assert ok is False
    assert value is None
    assert error == "Enter a guess."


def test_letters_are_rejected():
    ok, value, _ = parse_guess("abc", 1, 100)
    assert ok is False
    assert value is None


# --- A valid guess still works ---


def test_normal_guess_is_accepted():
    ok, value, error = parse_guess("50", 1, 100)
    assert ok is True
    assert value == 50
    assert error is None
