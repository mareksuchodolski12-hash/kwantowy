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
        "barrier",
    }
)

_QREG_PATTERN = re.compile(r"^qreg\s+(\w+)\[(\d+)\];$")
_CREG_PATTERN = re.compile(r"^creg\s+(\w+)\[(\d+)\];$")
_MEASURE_PATTERN = re.compile(r"^measure\s+(\w+)\[(\d+)\]\s*->\s*(\w+)\[(\d+)\]\s*;$")
_GATE_LINE_PATTERN = re.compile(r"^([a-z][a-z0-9]*)(?:\(.*?\))?\s+")
_QUBIT_REF = re.compile(r"(\w+)\[(\d+)\]")


class QasmValidationError(BaseModel):
    """Structured error returned when QASM validation fails."""

    error: str
    line: int | None = None


def _expand_statements(qasm: str) -> list[tuple[int, str]]:
    """Expand multi-statement lines into individual ``(lineno, statement)`` pairs.

    Handles the common case where multiple QASM statements appear on a single
    line separated by semicolons (e.g. the Bell circuit in the frontend demo).
    """
    statements: list[tuple[int, str]] = []
    for lineno, raw in enumerate(qasm.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("//"):
            continue
        parts = stripped.split(";")
        for i, part in enumerate(parts):
            s = part.strip()
            if not s:
                continue
            # Re-attach the semicolon for parts that originally had one.
            # The last element of split() only lacks a semicolon when the
            # original line did NOT end with one (i.e. a missing semicolon).
            if i < len(parts) - 1:
                s += ";"
            statements.append((lineno, s))
    return statements


def _validate_qubit_operands(
    stmt: str, qregs: dict[str, int], lineno: int
) -> QasmValidationError | None:
    """Check that every ``reg[index]`` reference targets a declared qreg with a valid index."""
    for reg_name, idx_str in _QUBIT_REF.findall(stmt):
        idx = int(idx_str)
        if reg_name not in qregs:
            return QasmValidationError(
                error=f"Undeclared quantum register: {reg_name}", line=lineno
            )
        if idx >= qregs[reg_name]:
            return QasmValidationError(
                error=f"Qubit index {idx} out of range for {reg_name}[{qregs[reg_name]}]",
                line=lineno,
            )
    return None


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

    statements = _expand_statements(qasm)
    qregs: dict[str, int] = {}  # name → size
    cregs: dict[str, int] = {}  # name → size
    total_qubits = 0

    for lineno, stmt in statements:
        # Skip known directives
        if stmt.startswith("OPENQASM") or stmt.startswith("include "):
            continue

        # --- Register declarations ---
        if stmt.startswith("qreg "):
            m = _QREG_PATTERN.match(stmt)
            if m is None:
                return QasmValidationError(error="Invalid qreg declaration", line=lineno)
            qregs[m.group(1)] = int(m.group(2))
            total_qubits += int(m.group(2))
            if total_qubits > MAX_QUBITS:
                return QasmValidationError(
                    error=f"Qubit register size {total_qubits} exceeds simulator limit of {MAX_QUBITS}",
                    line=lineno,
                )
            continue

        if stmt.startswith("creg "):
            cm = _CREG_PATTERN.match(stmt)
            if cm is None:
                return QasmValidationError(error="Invalid creg declaration", line=lineno)
            cregs[cm.group(1)] = int(cm.group(2))
            continue

        # --- Measure statements (handled before general gates) ---
        if stmt.startswith("measure "):
            if not stmt.endswith(";"):
                return QasmValidationError(error="Missing semicolon", line=lineno)
            mm = _MEASURE_PATTERN.match(stmt)
            if mm is None:
                return QasmValidationError(error="Invalid measure statement", line=lineno)
            qreg_name, qi = mm.group(1), int(mm.group(2))
            creg_name, ci = mm.group(3), int(mm.group(4))
            if qreg_name not in qregs:
                return QasmValidationError(
                    error=f"Undeclared quantum register: {qreg_name}", line=lineno
                )
            if qi >= qregs[qreg_name]:
                return QasmValidationError(
                    error=f"Qubit index {qi} out of range for {qreg_name}[{qregs[qreg_name]}]",
                    line=lineno,
                )
            if creg_name not in cregs:
                return QasmValidationError(
                    error=f"Undeclared classical register: {creg_name}", line=lineno
                )
            if ci >= cregs[creg_name]:
                return QasmValidationError(
                    error=f"Classical bit index {ci} out of range for {creg_name}[{cregs[creg_name]}]",
                    line=lineno,
                )
            continue

        # --- Gate / barrier lines ---
        gm = _GATE_LINE_PATTERN.match(stmt)
        if gm:
            gate_name = gm.group(1)
            if gate_name not in _SUPPORTED_GATES:
                return QasmValidationError(error=f"Unsupported gate: {gate_name}", line=lineno)
            if not stmt.endswith(";"):
                return QasmValidationError(error="Missing semicolon", line=lineno)
            err = _validate_qubit_operands(stmt, qregs, lineno)
            if err is not None:
                return err
            continue

        # If none of the above matched, the statement is unrecognised
        if stmt.endswith(";"):
            # Could be an unsupported directive – let it slide for forward compat
            continue

        return QasmValidationError(error="Invalid QASM syntax", line=lineno)

    return None
