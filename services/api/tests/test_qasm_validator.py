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
