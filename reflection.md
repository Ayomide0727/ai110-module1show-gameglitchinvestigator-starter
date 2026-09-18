# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it?
- List at least two concrete bugs you noticed at the start  
  (for example: "the hints were backwards").

-The hint said go lower when the answer was higher and higher when the answer is lower
-Easy mode had less attempts than normal mode
-after you click on new game it dosent let you submit a guess
-it accepts number beyound the range

**Bug Reproduction Log**

Document at least 3 bugs you found. Add rows as needed.

| Input | Expected Behavior | Actual Behavior | Console Output / Error |
|-------|-------------------|-----------------|------------------------|
|guess 5 (actual 16) | hint: go higher | hint: go lower|None |
|esay mode |attempts higher than normal and hard mode  | attempts less normal and higher than hard | none |
|input 200 for a range of 1 to 100 | invaild inputs | accepts it | None |
|click New Game after losing a game | game resets so I can guess again | "Game over" stays on screen and Submit Guess does nothing | None |

---

## 2. How did you use AI as a teammate?

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)? I used Claude Code inside VS Code
- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).  when I asked it to restore the (outcome, message) return, it caught that the old try/except branch compared str(guess) to secret as text, where "9" beats "10" — another way to get a wrong hint. I verified it by deleting that branch and running python -m pytest tests/ -v, which passed all 6 tests
- Give one example of an AI suggestion that was incorrect or misleading (including what the AI suggested and how you verified the result).  One suggestion that was misleading: refactoring check_guess to return only the label, with the hint text moved to a dictionary in app.py. It looked cleaner but broke the three starter tests, which I saw as AssertionError: assert ('Win', '🎉 Correct!') == 'Win', so I went back to returning both values.

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed? I decided a bug was really fixed when I could reproduce the old behavior, apply the fix, and then see the right behavior both in the running app and in pytest for the hint bug, guessing below the secret finally said "Go HIGHER!"
- Describe at least one test you ran (manual or using pytest)  
  and what it showed you about your code.- The main test I ran was test_hint_never_points_away_from_the_secret, which loops every guess from 1 to 100 against a secret of 50 and fails if the message points the wrong way
- Did AI help you design or understand any tests? How? Claude Code wrote that test and two narrower ones after I asked for a case targeting the hint bug, then ran them against a copy of the buggy check_guess to prove they weren't useless: 3 of the 6 failed there, and all 6 passed after the fix. That showed me the starter tests were the real gap  they only checked the outcome label and never the message, so a swapped hint passed them.

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?
New Game reset attempts and secret but left status as "won", and because session state survives every rerun, that stale value kept triggering st.stop() on each new run.

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
