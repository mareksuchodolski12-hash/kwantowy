import pytest
from quantum_contracts import JobState

from app.domain.state_machine import InvalidStateTransition, ensure_transition


def test_valid_transition() -> None:
    ensure_transition(JobState.SUBMITTED, JobState.QUEUED)


def test_invalid_transition() -> None:
    with pytest.raises(InvalidStateTransition):
        ensure_transition(JobState.SUBMITTED, JobState.SUCCEEDED)
