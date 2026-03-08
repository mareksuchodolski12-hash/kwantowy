from quantum_contracts import JobState

ALLOWED_TRANSITIONS: dict[JobState, set[JobState]] = {
    JobState.SUBMITTED: {JobState.QUEUED, JobState.FAILED},
    JobState.QUEUED: {JobState.RUNNING, JobState.FAILED},
    JobState.RUNNING: {JobState.SUCCEEDED, JobState.FAILED},
    JobState.SUCCEEDED: set(),
    JobState.FAILED: {JobState.QUEUED},
}


class InvalidStateTransition(Exception):
    pass


def ensure_transition(current: JobState, next_state: JobState) -> None:
    if next_state not in ALLOWED_TRANSITIONS[current]:
        raise InvalidStateTransition(f"invalid transition from {current.value} to {next_state.value}")
