import random
import streamlit as st

from logic_utils import (
    check_guess,
    get_range_for_difficulty,
    guess_closeness,
    parse_guess,
    proximity_label,
    update_score,
)

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")


def start_round(range_low, range_high):
    """Set up a fresh round inside the given range."""
    st.session_state.secret = random.randint(range_low, range_high)
    # Attempts was 1 on first load, which made the first game's "Attempts
    # left" one lower than every game started with New Game. Both are 0 now,
    # because both go through here.
    st.session_state.attempts = 0
    st.session_state.score = 0
    st.session_state.status = "playing"
    # History holds (guess, outcome) pairs so the sidebar can show the
    # direction arrow alongside the closeness bar.
    st.session_state.history = []


# A win needs no arrow: proximity_label already reads "🎯 Exact".
ARROWS = {"Too High": "↓", "Too Low": "↑", "Win": ""}


def render_history(slot, secret, range_low, range_high):
    """Draw the live Guess History into a sidebar container."""
    history = st.session_state.history
    with slot:
        if not history:
            st.caption("No guesses yet.")
            return

        for attempt, (guess, past_outcome) in enumerate(history, start=1):
            closeness = guess_closeness(guess, secret, range_low, range_high)
            parts = [f"#{attempt}", str(guess), ARROWS[past_outcome],
                     proximity_label(closeness)]
            st.progress(closeness, text=" ".join(p for p in parts if p))


# FIX (difficulty switch): the secret was only drawn when it was missing from
# session state, and nothing watched the sidebar, so switching difficulty
# mid-game kept the old secret. Going Normal -> Easy left a secret like 87
# that Easy's 1-20 range can never reach, and parse_guess now rejects every
# guess above 20, so the round was unwinnable. The attempt limit changed
# underneath the player too, which could show a negative "Attempts left".
if "difficulty" not in st.session_state:
    st.session_state.difficulty = difficulty
    start_round(low, high)
elif st.session_state.difficulty != difficulty:
    st.session_state.difficulty = difficulty
    start_round(low, high)
    st.warning(
        f"Difficulty changed to {difficulty}. "
        f"Started a new round between {low} and {high}."
    )

st.sidebar.divider()
st.sidebar.subheader("Guess History")
# Reserve the spot now, but fill it at the end of the script. Streamlit runs
# top to bottom, so drawing it here would show the list as it was BEFORE the
# guess being submitted on this run.
history_slot = st.sidebar.container()

st.subheader("Make a guess")

st.info(
    # Was hardcoded to "1 and 100", which invited out-of-range guesses on
    # Easy (1-20) and Hard (1-50).
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {attempt_limit - st.session_state.attempts}"
)

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

raw_guess = st.text_input(
    "Enter your guess:",
    key=f"guess_input_{difficulty}"
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

if new_game:
    # FIX (New Game did nothing): this used to reset attempts and secret but
    # leave status, score and history alone, so after a win or loss the
    # st.stop() below still fired and the Submit button did nothing. I found
    # this by playing; Claude Code traced it to the leftover status value.
    # It now calls start_round, so it cannot drift out of sync again.
    start_round(low, high)
    st.success("New game started.")
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    # st.stop() ends the run here, so fill the sidebar before it: a finished
    # round is exactly when you want to look back over your guesses.
    render_history(history_slot, st.session_state.secret, low, high)
    st.stop()

if submit:
    # parse_guess now knows the difficulty's range, and a rejected input no
    # longer costs an attempt or lands in the history as if it were a guess.
    ok, guess_int, error = parse_guess(raw_guess, low, high)

    if not ok:
        st.error(error)
    else:
        st.session_state.attempts += 1

        # This line used to pass str(secret) on every other attempt, which made
        # check_guess compare text instead of numbers — my own find, fixed
        # before I brought Claude Code in. It now unpacks check_guess's tuple.
        outcome, message = check_guess(guess_int, st.session_state.secret)

        st.session_state.history.append((guess_int, outcome))

        if show_hint:
            st.warning(message)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}"
                )

render_history(history_slot, st.session_state.secret, low, high)

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
