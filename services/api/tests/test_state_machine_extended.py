"""Extended state machine tests covering all valid transitions and edge cases."""

import pytest
from quantum_contracts import JobState

from app.domain.state_machine import InvalidStateTransition, ensure_transition

# --------------------------------------------------------------------------- #
# All valid transitions                                                       #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "current,next_state",
    [
        (JobState.SUBMITTED, JobState.QUEUED),
        (JobState.SUBMITTED, JobState.FAILED),
        (JobState.QUEUED, JobState.RUNNING),
        (JobState.QUEUED, JobState.FAILED),
        (JobState.RUNNING, JobState.SUCCEEDED),
        (JobState.RUNNING, JobState.FAILED),
        (JobState.FAILED, JobState.QUEUED),
    ],
)
def test_valid_transitions(current: JobState, next_state: JobState) -> None:
    # Should not raise
    ensure_transition(current, next_state)


# --------------------------------------------------------------------------- #
# Terminal states – no outgoing transitions allowed                           #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("next_state", list(JobState))
def test_succeeded_is_terminal(next_state: JobState) -> None:
    with pytest.raises(InvalidStateTransition):
        ensure_transition(JobState.SUCCEEDED, next_state)


# --------------------------------------------------------------------------- #
# Specific invalid transitions                                                #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "current,next_state",
    [
        (JobState.SUBMITTED, JobState.SUCCEEDED),
        (JobState.SUBMITTED, JobState.RUNNING),
        (JobState.QUEUED, JobState.SUBMITTED),
        (JobState.QUEUED, JobState.QUEUED),
        (JobState.RUNNING, JobState.QUEUED),
        (JobState.RUNNING, JobState.SUBMITTED),
        (JobState.FAILED, JobState.SUCCEEDED),
        (JobState.FAILED, JobState.RUNNING),
        (JobState.FAILED, JobState.SUBMITTED),
    ],
)
def test_invalid_transitions(current: JobState, next_state: JobState) -> None:
    with pytest.raises(InvalidStateTransition):
        ensure_transition(current, next_state)


# --------------------------------------------------------------------------- #
# Determinism: same input always produces the same outcome                    #
# --------------------------------------------------------------------------- #


def test_transition_is_deterministic() -> None:
    for _ in range(100):
        ensure_transition(JobState.SUBMITTED, JobState.QUEUED)
        with pytest.raises(InvalidStateTransition):
            ensure_transition(JobState.SUBMITTED, JobState.SUCCEEDED)
