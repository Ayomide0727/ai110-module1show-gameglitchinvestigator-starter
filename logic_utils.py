"""Pure game logic for the Glitchy Guesser.

These helpers started out inside ``app.py``. I asked Claude Code to move them
here so they can be imported and unit tested without Streamlit running, which
is what makes ``tests/test_edge_cases.py`` and ``tests/test_game_logic.py``
possible.

Nothing in this module touches Streamlit, reads session state, or performs
I/O. Every function is deterministic: the same arguments always produce the
same result. ``app.py`` owns all state and rendering.

The examples in each docstring are runnable::

    python -m doctest logic_utils.py -v
"""

import re

# int() refuses to convert a decimal string longer than this (Python 3.11+),
# so we check the length ourselves instead of letting it raise.
MAX_DIGITS = 4300

# ASCII digits only, with an optional sign. Deliberately strict: this rejects
# "50.9", "1e3", "1_0", "0x10" and Unicode digits like "٥", all of which the
# old int()/float() parsing quietly accepted.
_INTEGER_RE = re.compile(r"[+-]?[0-9]+")


def get_range_for_difficulty(difficulty: str):
    """Return the inclusive range of numbers a difficulty can hide.

    Args:
        difficulty: One of "Easy", "Normal" or "Hard". Any other value is
            treated as "Normal" so a typo in the sidebar cannot crash the app.

    Returns:
        A ``(low, high)`` tuple of ints, both ends inclusive.

    Examples:
        >>> get_range_for_difficulty("Easy")
        (1, 20)
        >>> get_range_for_difficulty("Hard")
        (1, 50)
        >>> get_range_for_difficulty("Lunatic")
        (1, 100)
    """
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


def _range_message(low, high):
    """Build the out-of-range error text, naming the bounds when known.

    Private helper for :func:`parse_guess`. When the caller supplied no
    bounds there is no range to quote, so the message falls back to the only
    thing that can still be said about the value.

    Args:
        low: Lowest allowed guess, or None if the caller gave no bounds.
        high: Highest allowed guess, or None.

    Returns:
        A player-facing message string.

    Examples:
        >>> _range_message(1, 20)
        'Enter a whole number between 1 and 20.'
        >>> _range_message(None, None)
        'That number is too large.'
    """
    if low is None or high is None:
        return "That number is too large."
    return f"Enter a whole number between {low} and {high}."


# FIX (edge cases): this used to do int(float(raw)) whenever the text held a
# ".", so "50.9" silently became 50 and could win against a secret of 50.
# Nothing checked the difficulty range either, so "-7" and "999999999999999"
# were accepted as real guesses. A bare except also reported "That is not a
# number." for digit strings past int()'s 4300-character conversion limit.
def parse_guess(raw: str, low: int = None, high: int = None):
    """Turn raw text from the input box into a validated integer guess.

    Never raises. Every rejection is reported through the return value so the
    caller can show the message and let the player try again. Surrounding
    whitespace is ignored, but anything that is not a plain ASCII integer is
    refused rather than coerced -- no decimals, no scientific notation, no hex
    and no Unicode digits.

    Args:
        raw: Text as typed by the player. May be None or empty.
        low: Lowest allowed guess. Omit to skip the range check.
        high: Highest allowed guess. Omit to skip the range check.

    Returns:
        A ``(ok, guess, error)`` tuple. On success, ``(True, int, None)``.
        On rejection, ``(False, None, str)``. ``ok`` is True if and only if
        ``guess`` is not None and ``error`` is None.

    Examples:
        >>> parse_guess("50", 1, 100)
        (True, 50, None)
        >>> parse_guess("  7  ", 1, 100)
        (True, 7, None)
        >>> parse_guess("101", 1, 100)
        (False, None, 'Enter a whole number between 1 and 100.')
        >>> parse_guess("50.9", 1, 100)
        (False, None, 'Whole numbers only - no decimals or symbols.')
        >>> parse_guess("", 1, 100)
        (False, None, 'Enter a guess.')
    """
    if raw is None:
        return False, None, "Enter a guess."

    text = raw.strip()
    if text == "":
        return False, None, "Enter a guess."

    if not _INTEGER_RE.fullmatch(text):
        return False, None, "Whole numbers only - no decimals or symbols."

    # A number this long is outside every difficulty range anyway, so report
    # it as out of range rather than letting int() raise on it.
    if len(text.lstrip("+-")) > MAX_DIGITS:
        return False, None, _range_message(low, high)

    value = int(text)

    in_range = low is None or high is None or low <= value <= high
    if not in_range:
        return False, None, _range_message(low, high)

    return True, value, None


def check_guess(guess, secret):
    """Compare a guess to the secret and say which way the player should move.

    The message always points *toward* the secret: a guess above it is told to
    go lower. Both arguments must already be ints -- comparing them as text
    was the original source of the wrong hints.

    Args:
        guess: The player's validated guess.
        secret: The number to find.

    Returns:
        An ``(outcome, message)`` tuple. ``outcome`` is "Win", "Too High" or
        "Too Low"; ``message`` is the player-facing hint for that outcome.

    Examples:
        >>> check_guess(50, 50)[0]
        'Win'
        >>> check_guess(60, 50)[0]
        'Too High'
        >>> check_guess(40, 50)[0]
        'Too Low'
        >>> check_guess(9, 10)[0]   # as text, "9" > "10" -- the old bug
        'Too Low'
    """
    # FIX (hint bug): the two messages were swapped, so a guess above the
    # secret was told "Go HIGHER!". I caught that by playing the game. When I
    # asked Claude Code to restore this tuple format, it pointed out the old
    # try/except branch compared str(guess) to secret as text ("9" > "10" is
    # True) — a second wrong-hint path — so I dropped the branch instead.
    if guess == secret:
        return "Win", "🎉 Correct!"

    if guess > secret:
        return "Too High", "📉 Go LOWER!"
    return "Too Low", "📈 Go HIGHER!"


# Closeness bands for the Guess History sidebar, checked high to low. The
# thresholds are fractions of the range, so they scale with difficulty: on
# Normal (1-100) "Blazing" means within 5, on Easy (1-20) it means within 1.
PROXIMITY_BANDS = [
    (1.00, "🎯 Exact"),
    (0.94, "🔥 Blazing"),
    (0.88, "♨️ Hot"),
    (0.78, "🌤️ Warm"),
    (0.62, "❄️ Cool"),
    (0.00, "🧊 Freezing"),
]


def guess_closeness(guess: int, secret: int, low: int, high: int) -> float:
    """Score how close a guess landed, as a fraction of the range.

    Measured against the width of the range rather than an absolute distance,
    so the result means the same thing on every difficulty: being 5 away is a
    near miss on Normal (1-100) but a poor guess on Easy (1-20).

    Args:
        guess: The guess to score.
        secret: The number to find.
        low: Lowest number in the range.
        high: Highest number in the range.

    Returns:
        A float from 0.0 to 1.0, where 1.0 is exactly right and 0.0 is as far
        away as the range allows. Safe to pass straight to ``st.progress``.

    Examples:
        >>> guess_closeness(55, 55, 1, 100)
        1.0
        >>> round(guess_closeness(60, 55, 1, 100), 3)
        0.949
        >>> guess_closeness(1, 100, 1, 100)
        0.0
        >>> guess_closeness(5, 5, 5, 5)   # degenerate one-number range
        1.0
    """
    span = high - low
    if span <= 0:
        # A one-number range: the guess is either right or it is not.
        return 1.0 if guess == secret else 0.0

    closeness = 1.0 - abs(guess - secret) / span
    # parse_guess keeps guesses inside the range, but clamp anyway so a stray
    # value can never hand Streamlit a progress fraction outside 0.0-1.0.
    return min(1.0, max(0.0, closeness))


def proximity_label(closeness: float) -> str:
    """Describe a closeness score in hot/cold words for the sidebar.

    Args:
        closeness: A score from :func:`guess_closeness`, 0.0 to 1.0.

    Returns:
        The label of the highest band the score reaches, from "🧊 Freezing"
        up to "🎯 Exact". See :data:`PROXIMITY_BANDS` for the thresholds.

    Examples:
        >>> proximity_label(1.0).endswith("Exact")
        True
        >>> proximity_label(0.95).endswith("Blazing")
        True
        >>> proximity_label(0.10).endswith("Freezing")
        True
    """
    for threshold, label in PROXIMITY_BANDS:
        if closeness >= threshold:
            return label
    return PROXIMITY_BANDS[-1][1]


def update_score(current_score: int, outcome: str, attempt_number: int):
    """Apply one round's outcome to the running score.

    A win is worth more the sooner it comes, never dropping below a floor of
    10 points. A wrong guess costs 5.

    Known oddity, left as found: a "Too High" guess on an even-numbered
    attempt *adds* 5 instead of subtracting it, so a wrong guess can be
    rewarded. It is asymmetric with "Too Low" and looks unintentional, but it
    is scoring behaviour rather than an input bug, so it is documented here
    rather than silently changed.

    Args:
        current_score: Score before this guess.
        outcome: "Win", "Too High" or "Too Low". Anything else is ignored.
        attempt_number: Which attempt this was, counting from 1.

    Returns:
        The new score as an int. May be negative.

    Examples:
        >>> update_score(0, "Win", 1)
        80
        >>> update_score(0, "Win", 9)       # floor holds
        10
        >>> update_score(0, "Too Low", 3)
        -5
        >>> update_score(0, "Too High", 2)  # the oddity described above
        5
        >>> update_score(42, "Sideways", 3)
        42
    """
    if outcome == "Win":
        points = 100 - 10 * (attempt_number + 1)
        if points < 10:
            points = 10
        return current_score + points

    if outcome == "Too High":
        if attempt_number % 2 == 0:
            return current_score + 5
        return current_score - 5

    if outcome == "Too Low":
        return current_score - 5

    return current_score
