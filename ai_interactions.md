# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

Agent: Claude Code (Opus 5), running in VS Code with file-edit approval on, so
every write was proposed to me before it was applied.

**What task did you give the agent?**

Four asks, each building on the last:

1. Find edge case inputs that could still break the game, and write pytest
   cases proving it handles them gracefully.
2. Apply the fixes those tests demanded.
3. Fix the difficulty-switch bug the agent flagged while doing (2).
4. Implement a "Guess History" sidebar that visualizes how close each
   previous guess was.

**What did the agent do?**

| File | Change |
|---|---|
| `logic_utils.py` | Rewrote `parse_guess` to take `low`/`high`, match a strict `[+-]?[0-9]+` regex instead of `int(float(...))`, and length-check before `int()`. Added `guess_closeness`, `proximity_label`, `PROXIMITY_BANDS` for the sidebar. |
| `app.py` | Added `start_round()` and a difficulty guard; made the banner show the real range; moved the attempt counter below validation; changed history to `(guess, outcome)` pairs; added `render_history()` and a reserved sidebar container. |
| `tests/test_edge_cases.py` | New file. Agent drafted it; I rewrote it (see SF7). |
| `ai_interactions.md` | This log and SF7. |

Commands it ran: `pytest` after every change, `py_compile`, and
`streamlit.testing.v1.AppTest` to drive the actual app through a difficulty
switch, a loss, New Game, and a rejected input.

**What did you have to verify or fix manually?**

- **I rewrote the whole test file.** Its first version was 59 parametrized
  tests whose output was unreadable — pytest builds test IDs from parameter
  values, so a 5000-digit input printed as one enormous line. I asked for a
  cleanup, then rewrote it myself in the plain style of `test_game_logic.py`.
- **I cut its first draft of the SF7 log**, which padded my four-column table
  with extra commentary I had not asked for.
- **I made it explain the feature before building it.** I stopped its first
  edit for the Guess History and asked what the sidebar would actually show;
  it produced a mock-up, and I confirmed I wanted the closeness bars live
  during play rather than hidden until the round ended.
- **Design call it raised, I decided:** switching difficulty mid-round now
  discards the round. It asked rather than assuming.
- **Bugs it caught in its own work** (via the `AppTest` run, not by my
  reading): the win row rendered a duplicated 🎯, and its first proximity
  bands were miscalibrated so a guess 35 away on a 1-100 range read as
  "Cool". Both fixed before I saw the app.
- **Not covered by tests:** the difficulty fix and the sidebar live in
  Streamlit session state, so `pytest` does not touch them. They were
  verified by the `AppTest` runs and by playing the app.

---

## Test Generation (SF7)

> Document how you used AI to help generate or improve tests.

Assistant: Claude Code (Opus 5). Tests live in `tests/test_edge_cases.py`.
I gave three prompts, in this order:

```
P1  Identify three potential edge case inputs (e.g., negative numbers,
    decimals, or extremely large values) that might still break my game.

P2  Generate a suite of pytest cases that verify my game handles these
    inputs gracefully.

P3  Rewrite tests/test_edge_cases.py in the same plain style as
    test_game_logic.py - one test per invalid input, no parametrize.
```

Before writing anything, P1 made the assistant run each candidate input
through the real `parse_guess`, so the three cases below are behaviour I
confirmed, not guesses. I asked for the tests first and the fix second, so I
could watch them fail against the old `parse_guess`.

| Edge Case | Prompt | AI-Suggested Test | Did It Pass? | Your Reasoning |
|---|---|---|---|---|
| Out-of-range: `-7`, `0`, `101` | P1 → P2 | `test_negative_number_is_rejected` | No — passes after `parse_guess` took `low`/`high` | `get_range_for_difficulty` existed but nothing compared a guess to it, so `-7` burned an attempt on a useless "Go HIGHER!" |
| Decimals: `50.9`, `0.0000001` | P1 → P2 | `test_decimal_is_rejected` | No — passes after dropping `int(float(...))` | `int(float("50.9"))` was `50`, so a decimal could **win** against a secret of 50 |
| Huge values: 21- and 5000-digit | P1 → P2 | `test_huge_number_is_rejected` | No — passes after a digit-length guard | Python 3.11+ caps `int()` at 4300 digits, so the bare `except` called a valid number "not a number" |
| Bonus — looks numeric: `1e3`, `0x10` | P2 | `test_scientific_notation_is_rejected` | No — passes after the strict `[+-]?[0-9]+` regex | The old parser branched on a `.`, so `1e3` was rejected while `1.5e3` became `1500` |

Full suite: 14 tests in `tests/test_edge_cases.py`, all passing.

---

## Linting & Style (SF9)

> Document your use of AI for linting or code style improvements.

**Prompt used:**

```
P1  Review your code for PEP 8 style compliance.

P2  Resolve any formatting or naming issues.
```

No linter was installed, so P1 made the agent add `pycodestyle` and `pylint`
to `.venv` and report real findings instead of its own opinion. Neither is a
runtime dependency, so `requirements.txt` is unchanged.

**Linting output before:**

Full output, before and after, is committed as `lint_output.txt`. Summary:

```
$ python -m pycodestyle --max-line-length=79 --statistics app.py logic_utils.py tests/
21      E302 expected 2 blank lines, found 1
2       E501 line too long (83 > 79 characters)
   (logic_utils.py: zero violations)

$ python -m pylint --enable=C0103,W0621,C0325,W0611,W0612 ...
app.py:39,57: W0621 Redefining name 'low'/'high' from outer scope   (x4)
app.py:65:    W0621 Redefining name 'outcome' from outer scope
logic_utils.py:134: C0325 Unnecessary parens after 'not' keyword
Your code has been rated at 9.74/10
```

After: `pycodestyle` exits 0, pylint rates 10.00/10.

**Changes applied:**

| Suggested | Applied? |
|---|---|
| `E302` — two blank lines between functions (23 spots) | Yes |
| `E501` — two 83-char assertion messages in `test_game_logic.py` | Yes, by shortening the messages rather than wrapping the lines |
| `C0325` — drop the parens in `not (low <= value <= high)` | Yes, but as a named `in_range` condition instead of bare removal, which reads better than either |
| `W0621` — rename shadowed params: `low`/`high` → `range_low`/`range_high`, loop `outcome` → `past_outcome` | Yes |
| `_INTEGER` → `_INTEGER_RE` (holds a compiled pattern, not an int) | Yes — agent's own catch, no linter flagged it |
| `err` → `error`, loop `number` → `attempt` | Yes — readability, not linter findings |
| Add a `requirements-dev.txt` for the two linters | Not yet |

**Where I overruled it.** On P1 the agent fixed only its own `E302` in
`app.py` and argued the other 22 findings should stand, on the grounds that
one blank line between tests was the starter file's convention and PEP 8 says
"know when to be inconsistent". I disagreed — a style section is worth more
at zero findings than with an argument attached — so P2 told it to resolve
everything. After the renames it re-ran pytest, the doctests, and an `AppTest`
play-through to confirm nothing broke: 20 tests, 24 doctests, 0 exceptions.

---

## Model Comparison (SF11)

> Compare two AI models on the same task.

**Task given to both models:**

<!-- Describe what you asked each model to do -->

| | Model A | Model B |
|-|---------|---------|
| **Model name** | | |
| **Response summary** | | |
| **More Pythonic?** | | |
| **Clearer explanation?** | | |

**Which did you prefer and why?**

<!-- Your conclusion -->
