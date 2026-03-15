"""Lightweight QASM 2.0 syntax and semantic validation.

Validates circuits before they enter the execution queue, rejecting early if
the syntax is broken, unsupported gates are used, or the qubit register
exceeds simulator limits.
"""

from __future__ import annotations

import re

from pydantic import BaseModel

# Maximum qubit register size accepted by the local simulators.
MAX_QUBITS = 30

_SUPPORTED_GATES = frozenset(
    {
        "x",
        "y",
        "z",
        "h",
        "s",
        "t",
        "cx",
        "cz",
        "ccx",
        "swap",
        "rx",
        "ry",
        "rz",
        "u1",
        "u2",
        "u3",
        "sdg",
        "tdg",
        "id",
        "measure",
        "barrier",
    }
)

_QREG_PATTERN = re.compile(r"^qreg\s+\w+\[(\d+)\];$")
_GATE_LINE_PATTERN = re.compile(r"^([a-z][a-z0-9]*)(?:\(.*?\))?\s+")


class QasmValidationError(BaseModel):
    """Structured error returned when QASM validation fails."""

    error: str
    line: int | None = None


def validate_qasm(qasm: str) -> QasmValidationError | None:
    """Validate an OpenQASM 2.0 circuit string.

    Returns ``None`` when the circuit is valid, or a
    :class:`QasmValidationError` describing the first problem found.
    """
    lines = qasm.splitlines()
    if not lines:
        return QasmValidationError(error="Empty QASM circuit")

    # --- Header check ---
    stripped_first = lines[0].strip()
    if not stripped_first.startswith("OPENQASM"):
        return QasmValidationError(error="Missing OPENQASM header", line=1)

    total_qubits = 0

    for lineno, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("//"):
            continue

        # Skip known directives
        if stripped.startswith("OPENQASM") or stripped.startswith("include "):
            continue

        # Register declarations
        if stripped.startswith("qreg "):
            m = _QREG_PATTERN.match(stripped)
            if m is None:
                return QasmValidationError(error="Invalid qreg declaration", line=lineno)
            total_qubits += int(m.group(1))
            if total_qubits > MAX_QUBITS:
                return QasmValidationError(
                    error=f"Qubit register size {total_qubits} exceeds simulator limit of {MAX_QUBITS}",
                    line=lineno,
                )
            continue

        if stripped.startswith("creg "):
            # Simple creg validation – just accept well-formed declarations
            if not re.match(r"^creg\s+\w+\[\d+\];$", stripped):
                return QasmValidationError(error="Invalid creg declaration", line=lineno)
            continue

        # Gate / measure / barrier lines
        gm = _GATE_LINE_PATTERN.match(stripped)
        if gm:
            gate_name = gm.group(1)
            if gate_name not in _SUPPORTED_GATES:
                return QasmValidationError(error=f"Unsupported gate: {gate_name}", line=lineno)
            # Check trailing semicolon
            if not stripped.endswith(";"):
                return QasmValidationError(error="Missing semicolon", line=lineno)
            continue

        # If none of the above matched, the line is unrecognised
        if stripped.endswith(";"):
            # Could be an unsupported directive – let it slide for forward compat
            continue

        return QasmValidationError(error="Invalid QASM syntax", line=lineno)

    return None
