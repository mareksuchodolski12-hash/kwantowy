"""Tests for the QASM validation service."""

from app.services.qasm_validator import validate_qasm


class TestValidQasm:
    def test_valid_bell_state(self) -> None:
        qasm = (
            'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n'
            "h q[0];\ncx q[0],q[1];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];"
        )
        assert validate_qasm(qasm) is None

    def test_valid_ghz_state(self) -> None:
        qasm = (
            'OPENQASM 2.0;\ninclude "qelib1.inc";\n\nqreg q[3];\ncreg c[3];\n\n'
            "h q[0];\ncx q[0],q[1];\ncx q[1],q[2];\n\n"
            "measure q[0] -> c[0];\nmeasure q[1] -> c[1];\nmeasure q[2] -> c[2];"
        )
        assert validate_qasm(qasm) is None

    def test_valid_single_qubit(self) -> None:
        qasm = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\ncreg c[1];\nx q[0];\nmeasure q[0] -> c[0];'
        assert validate_qasm(qasm) is None

    def test_valid_parameterised_gate(self) -> None:
        qasm = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\ncreg c[1];\nrx(1.57) q[0];\nmeasure q[0] -> c[0];'
        assert validate_qasm(qasm) is None

    def test_valid_minimal_measure_only(self) -> None:
        """Minimal valid circuit: declare, measure, done."""
        qasm = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\ncreg c[1];\nmeasure q[0] -> c[0];'
        assert validate_qasm(qasm) is None

    def test_valid_single_line_bell(self) -> None:
        """Single-line Bell state (as used in the frontend demo)."""
        qasm = (
            'OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; creg c[2]; '
            "h q[0]; cx q[0],q[1]; measure q[0] -> c[0]; measure q[1] -> c[1];"
        )
        assert validate_qasm(qasm) is None


class TestInvalidQasm:
    def test_empty_circuit(self) -> None:
        result = validate_qasm("")
        assert result is not None
        assert result.error == "Empty QASM circuit"

    def test_missing_header(self) -> None:
        result = validate_qasm("qreg q[2];")
        assert result is not None
        assert result.error == "Missing OPENQASM header"
        assert result.line == 1

    def test_unsupported_gate(self) -> None:
        qasm = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\nfoobar q[0],q[1];'
        result = validate_qasm(qasm)
        assert result is not None
        assert "Unsupported gate" in result.error
        assert result.line == 5

    def test_qubit_limit_exceeded(self) -> None:
        qasm = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[31];'
        result = validate_qasm(qasm)
        assert result is not None
        assert "exceeds simulator limit" in result.error
        assert result.line == 3

    def test_invalid_qreg_declaration(self) -> None:
        qasm = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q;'
        result = validate_qasm(qasm)
        assert result is not None
        assert "Invalid qreg" in result.error

    def test_boundary_qubit_count_accepted(self) -> None:
        qasm = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[30];\ncreg c[30];\nh q[0];'
        result = validate_qasm(qasm)
        assert result is None

    def test_comments_are_ignored(self) -> None:
        qasm = 'OPENQASM 2.0;\ninclude "qelib1.inc";\n// this is a comment\nqreg q[1];\ncreg c[1];\nh q[0];'
        result = validate_qasm(qasm)
        assert result is None

    # --- new validation tests ---

    def test_missing_semicolon(self) -> None:
        """Gate statement without a trailing semicolon."""
        qasm = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\ncreg c[1];\nh q[0]'
        result = validate_qasm(qasm)
        assert result is not None
        assert "Missing semicolon" in result.error

    def test_qubit_index_out_of_range(self) -> None:
        qasm = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\nh q[5];'
        result = validate_qasm(qasm)
        assert result is not None
        assert "out of range" in result.error

    def test_classical_bit_index_out_of_range(self) -> None:
        qasm = (
            'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[1];\n'
            "measure q[0] -> c[5];"
        )
        result = validate_qasm(qasm)
        assert result is not None
        assert "out of range" in result.error

    def test_invalid_creg_declaration(self) -> None:
        qasm = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c;'
        result = validate_qasm(qasm)
        assert result is not None
        assert "Invalid creg" in result.error

    def test_invalid_measure_target(self) -> None:
        """Measure without a proper ``->`` classical target."""
        qasm = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\ncreg c[1];\nmeasure q[0];'
        result = validate_qasm(qasm)
        assert result is not None
        assert "Invalid measure" in result.error

    def test_undeclared_qreg_in_gate(self) -> None:
        qasm = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\nh r[0];'
        result = validate_qasm(qasm)
        assert result is not None
        assert "Undeclared quantum register" in result.error

    def test_undeclared_creg_in_measure(self) -> None:
        qasm = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\ncreg c[1];\nmeasure q[0] -> x[0];'
        result = validate_qasm(qasm)
        assert result is not None
        assert "Undeclared classical register" in result.error

    def test_single_line_invalid_gate(self) -> None:
        """Multi-statement single line with an unsupported gate must be caught."""
        qasm = (
            'OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; creg c[2]; '
            "h q[0]; foobar q[0],q[1]; measure q[0] -> c[0];"
        )
        result = validate_qasm(qasm)
        assert result is not None
        assert "Unsupported gate" in result.error
