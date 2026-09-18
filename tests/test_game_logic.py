from logic_utils import check_guess


def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    outcome, _ = check_guess(50, 50)
    assert outcome == "Win"


def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    outcome, _ = check_guess(60, 50)
    assert outcome == "Too High"


def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    outcome, _ = check_guess(40, 50)
    assert outcome == "Too Low"


# The three tests above came with the starter and only check the outcome label.
# I asked Claude Code for a case targeting the hint bug specifically; it wrote
# the three below and then ran them against a copy of the buggy check_guess to
# show they really fail on it. That was the gap — the starter tests never
# looked at the message, so a swapped hint passed them.

def test_too_high_hint_says_go_lower():
    # The hint bug: a guess ABOVE the secret was told "Go HIGHER!",
    # sending the player further away from the answer.
    outcome, message = check_guess(60, 50)
    assert outcome == "Too High"
    assert message == "📉 Go LOWER!"


def test_too_low_hint_says_go_higher():
    outcome, message = check_guess(40, 50)
    assert outcome == "Too Low"
    assert message == "📈 Go HIGHER!"


def test_hint_never_points_away_from_the_secret():
    # Sweep the whole Normal range. No guess should ever get a hint
    # that points away from the secret.
    secret = 50
    for guess in range(1, 101):
        outcome, message = check_guess(guess, secret)
        if guess > secret:
            assert message == "📉 Go LOWER!", f"{guess} was sent higher"
        elif guess < secret:
            assert message == "📈 Go HIGHER!", f"{guess} was sent lower"
        else:
            assert outcome == "Win"
