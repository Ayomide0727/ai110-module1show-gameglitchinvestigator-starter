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

**Fixes applied**

- [x] Guarded the secret behind `if "secret" not in st.session_state` so it
      persists across reruns and is only redrawn on New Game.
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

## 🚀 Stretch Features

- [ ] [If you choose to complete Challenge 4, describe the Enhanced UI changes here — a screenshot is optional]
