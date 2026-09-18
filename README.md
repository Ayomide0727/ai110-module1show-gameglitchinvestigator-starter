# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🚨 The Situation

You asked an AI to build a simple "Number Guessing Game" using Streamlit.
It wrote the code, ran away, and now the game is unplayable. 

- You can't win.
- The hints lie to you.
- The secret number seems to have commitment issues.

## 🛠️ Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run the broken app: `python -m streamlit run app.py`

## 🕵️‍♂️ Your Mission

1. **Play the game.** Open the "Developer Debug Info" tab in the app to see the secret number. Try to win.
2. **Find the State Bug.** Why does the secret number change every time you click "Submit"? Ask ChatGPT: *"How do I keep a variable from resetting in Streamlit when I click a button?"*
3. **Fix the Logic.** The hints ("Higher/Lower") are wrong. Fix them.
4. **Refactor & Test.** - Move the logic into `logic_utils.py`.
   - Run `pytest` in your terminal.
   - Keep fixing until all tests pass!

## 📝 Document Your Experience

**Purpose of the game**

A number guessing game built with Streamlit. The app picks a secret number
inside a range set by the difficulty (Easy 1-20, Normal 1-100, Hard 1-50) and
the player has a limited number of attempts to find it. After each guess the
game says whether to go higher or lower, updates a score, and ends on a win or
when attempts run out. New Game starts a fresh round.

**Bugs found**

- [x] State bug: the secret number was re-rolled on every rerun, so it changed
      each time Submit was clicked and the game could never be won.
- [x] Hint bug: the "Go HIGHER" and "Go LOWER" messages were swapped, so a
      guess above the secret was told to go higher.
- [x] String comparison: on some attempts the secret was passed to
      `check_guess` as a string, so the comparison ran on text instead of
      numbers ("9" > "10" is True) — a second source of wrong hints.
- [x] New Game did nothing after a round finished: it reset the secret and
      attempts but left `status`, score, and history, so the game stayed locked
      and Submit kept doing nothing.
- [x] Attempt counter started at 1 instead of 0, so the first game showed one
      fewer attempt than every game started with New Game.
- [x] Test gap: the starter tests only checked the outcome label, never the
      hint text, so the swapped hints passed the test suite.

Found later, while hunting edge cases with the AI assistant:

- [x] No range check: `get_range_for_difficulty` existed, but nothing ever
      compared a guess to it. `-7`, `0` and `999999999999999` were all
      accepted as real guesses, burning an attempt for a hint that was
      technically true and completely useless.
- [x] Decimals were truncated, not rejected: `int(float("50.9"))` is `50`, so
      guessing `50.9` **won** against a secret of 50 — a number the player
      never typed — and the history logged it as `50`.
- [x] Misleading error on very long numbers: Python 3.11+ caps `int()` string
      conversion at 4300 digits, and a bare `except` turned that into "That is
      not a number." about a perfectly valid number.
- [x] Inconsistent parsing: the parser branched on whether the text contained
      a `.`, so `1e3` was rejected while `1.5e3` quietly became `1500`.
- [x] Typos cost a turn: an invalid entry incremented the attempt counter and
      was appended to the history as though it were a guess.
- [x] Difficulty switch left a stale secret: the secret was only drawn when
      missing from session state and nothing watched the sidebar, so going
      Normal → Easy kept a secret like 87 that Easy's 1-20 range can never
      reach. Adding the range check turned this from confusing into an
      unwinnable round.
- [x] The "Guess a number between 1 and 100" banner was hardcoded, so it lied
      on Easy and Hard and invited out-of-range guesses.

**Fixes applied**

- [x] Guarded the secret behind `if "secret" not in st.session_state` so it
      persists across reruns instead of being re-rolled on every submit.
      (This guard was later folded into `start_round()` — see below.)
- [x] Corrected the two hint messages in `check_guess` and removed the
      try/except branch that compared values as strings.
- [x] Made `check_guess` always return a `(outcome, message)` tuple and had
      `app.py` pass the integer secret and unpack it.
- [x] Made New Game reset everything: secret, attempts, score, status, and
      history, followed by `st.rerun()`.
- [x] Initialized attempts to 0 to match the New Game reset.
- [x] Refactored `get_range_for_difficulty`, `parse_guess`, `check_guess`, and
      `update_score` out of `app.py` into `logic_utils.py` so they can be
      imported and unit tested without running Streamlit.
- [x] Added three tests that assert on the hint text itself, including one that
      sweeps all of 1-100 to confirm no guess is ever pointed away from the
      secret.

For the bugs found later:

- [x] Rewrote `parse_guess` to take `low`/`high` and enforce them, to match a
      strict `[+-]?[0-9]+` regex instead of `int(float(...))`, and to
      length-check the text before calling `int()` on it. Every rejection now
      returns a message that says what to do.
- [x] Replaced the five separate `if "x" not in st.session_state` blocks with
      one `start_round()` in `app.py`, called from all three places a round
      begins: first load, New Game, and a difficulty change. The drift between
      those paths was the same bug class as the original New Game bug, so
      there is now a single definition of "a fresh round".
- [x] Added a difficulty guard that compares the sidebar against
      `st.session_state.difficulty` and starts a new round when they differ,
      with an `st.warning` explaining why.
- [x] Moved the attempt counter below validation and stopped appending
      rejected input to the history.
- [x] Made the info banner read the real `low`/`high`.
- [x] Added 14 edge case tests in `tests/test_edge_cases.py`, written *before*
      the parser fix so they could be watched failing against the old code.
- [x] Documented every function in `logic_utils.py` with Google-style
      docstrings whose examples are runnable: `python -m doctest logic_utils.py`
      executes 24 of them.

**Known issue, documented rather than fixed**

`update_score` gives **+5 for a wrong "Too High" guess on an even-numbered
attempt**, which is asymmetric with "Too Low" and looks unintentional. It is
scoring behaviour rather than an input or state bug, so it is recorded in the
function's docstring and pinned by a doctest instead of being silently
changed.

## 📸 Demo Walkthrough

Sample game on Normal difficulty (range 1-100, 8 attempts). The secret was 55,
read from the Developer Debug Info panel.

1. User enters a guess of 40 → "Go HIGHER" (attempts left 7, score -5)
2. User enters a guess of 70 → "Go LOWER" (attempts left 6, score 0)
3. Debug panel still shows Secret 55, confirming the number no longer changes
   between submits
4. User enters a guess of 55 → "Correct!" and the game ends with "You won! The
   secret was 55. Final score: 60"
5. Further guesses are rejected until the user clicks New Game, which resets the
   secret, score, attempts, and history


## 🧪 Test Results

```
# Paste your pytest output here, e.g.:
# pytest tests/
# ========================= X passed in 0.XXs =========================
```
============================================================================= test session starts ==============================================================================
platform win32 -- Python 3.12.8, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\ayomi\C0SC491\ai110-module1show-gameglitchinvestigator-starter\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\ayomi\C0SC491\ai110-module1show-gameglitchinvestigator-starter
plugins: anyio-4.15.0
collected 20 items     

tests/test_edge_cases.py::test_negative_number_is_rejected PASSED                     [5%]
tests/test_edge_cases.py::test_zero_is_rejected PASSED                                [10%]
tests/test_edge_cases.py::test_number_above_the_range_is_rejected PASSED              [15%]
tests/test_edge_cases.py::test_error_message_names_the_real_bounds PASSED             [20%]
tests/test_edge_cases.py::test_decimal_is_rejected PASSED                             [25%]
tests/test_edge_cases.py::test_tiny_decimal_is_rejected PASSED                        [30%]
tests/test_edge_cases.py::test_huge_number_is_rejected PASSED                         [35%]
tests/test_edge_cases.py::test_very_long_number_is_not_called_not_a_number PASSED     [40%]
tests/test_edge_cases.py::test_check_guess_compares_big_numbers_as_numbers PASSED     [45%]
tests/test_edge_cases.py::test_scientific_notation_is_rejected PASSED                 [50%]
tests/test_edge_cases.py::test_hex_is_rejected PASSED                                 [55%]
tests/test_edge_cases.py::test_empty_input_is_rejected PASSED                         [60%]
tests/test_edge_cases.py::test_letters_are_rejected PASSED                            [65%]
tests/test_edge_cases.py::test_normal_guess_is_accepted PASSED                        [70%]
tests/test_game_logic.py::test_winning_guess PASSED                                   [75%]
tests/test_game_logic.py::test_guess_too_high PASSED                                  [80%]
tests/test_game_logic.py::test_guess_too_low PASSED                                   [85%]
tests/test_game_logic.py::test_too_high_hint_says_go_lower PASSED                     [90%]
tests/test_game_logic.py::test_too_low_hint_says_go_higher PASSED                     [95%]
tests/test_game_logic.py::test_hint_never_points_away_from_the_secret PASSED          [100%]
==================================== 20 passed in 0.07s ====================================

## 🚀 Stretch Features

### Challenge 4: Enhanced Game UI

- [x] **Guess History sidebar with Hot/Cold visualization**

The main enhancement. Every guess stays listed in the sidebar for the whole
round, showing the number guessed, a direction arrow, a Hot/Cold label, and a
bar whose length is how close that guess landed. Here is a real round on
Normal with the secret at 55:

```
Guess History

#1 20 ↑ 🧊 Freezing   |########            |  42%
#2 90 ↓ ❄️ Cool       |#############       |  64%
#3 60 ↓ 🔥 Blazing    |################### |  94%
#4 55   🎯 Exact      |####################| 100%
```

| Where | What it does now |
|---|---|
| `guess_closeness(guess, secret, low, high)` in `logic_utils.py` | New. Returns how close a guess was as a 0.0-1.0 fraction of the range, so it means the same thing on every difficulty. Feeds `st.progress` directly. |
| `proximity_label(closeness)` in `logic_utils.py` | New. Maps that fraction to 🧊 Freezing → ❄️ Cool → 🌤️ Warm → ♨️ Hot → 🔥 Blazing → 🎯 Exact. |
| `PROXIMITY_BANDS` in `logic_utils.py` | New. The thresholds, as fractions of the range: "Blazing" is within 5 on Normal (1-100) but within 1 on Easy (1-20). |
| `render_history(slot, secret, range_low, range_high)` in `app.py` | New. Draws one `st.progress` bar per guess, or "No guesses yet." when the round is fresh. |
| `st.session_state.history` in `app.py` | Now stores `(guess, outcome)` pairs instead of bare ints, so the sidebar can show the ↑/↓ arrow. |

The history is drawn into a reserved `st.sidebar.container()` that is filled
at the *end* of the script. Streamlit runs top to bottom, so drawing it where
it appears would have shown the list as it was before the guess being
submitted on that run — every row one step stale. It is also filled just
before the `st.stop()` on the game-over screen, so a finished round can still
be reviewed.

- [x] **Clearer, range-accurate feedback**

| Where | What it does now |
|---|---|
| `st.info` banner in `app.py` | Was hardcoded to "between 1 and 100" on every difficulty; now reads the real `low`/`high`, so Easy says 1 to 20. |
| `parse_guess` error text in `logic_utils.py` | Replaced "That is not a number." with messages that say what to do: "Enter a whole number between 1 and 20." and "Whole numbers only - no decimals or symbols." |
| `st.warning` on difficulty change in `app.py` | New. Says the round restarted and in what range, instead of silently swapping the range out from under the player. |
| Submit handler in `app.py` | A rejected input no longer costs an attempt or appears in the history as though it were a guess. |

**Core logic untouched.** `check_guess` and `update_score` behave exactly as
before — all 20 tests, including the six in `test_game_logic.py` that pin the
hint text, pass unchanged. The new UI functions are pure and have their own
docstring examples (`python -m doctest logic_utils.py`).
