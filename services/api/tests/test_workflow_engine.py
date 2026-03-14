"""Tests for workflow orchestration engine (component 5)."""

from quantum_contracts import (
    CircuitPayload,
    WorkflowDefinition,
    WorkflowStep,
)

from app.services.workflow_engine import KNOWN_ACTIONS, topological_sort, validate_workflow

QASM = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\ncreg c[1];\nx q[0];\nmeasure q[0] -> c[0];'


class TestValidateWorkflow:
    def test_valid_workflow(self) -> None:
        defn = WorkflowDefinition(
            name="test-wf",
            steps=[
                WorkflowStep(name="simulate", action="simulate"),
                WorkflowStep(name="optimise", action="optimise", depends_on=["simulate"]),
                WorkflowStep(name="run", action="hardware_run", depends_on=["optimise"]),
            ],
            circuit=CircuitPayload(qasm=QASM, shots=100),
        )
        errors = validate_workflow(defn)
        assert errors == []

    def test_unknown_action(self) -> None:
        defn = WorkflowDefinition(
            name="bad-action",
            steps=[WorkflowStep(name="s1", action="nonexistent")],
            circuit=CircuitPayload(qasm=QASM, shots=100),
        )
        errors = validate_workflow(defn)
        assert any("unknown action" in e for e in errors)

    def test_unknown_dependency(self) -> None:
        defn = WorkflowDefinition(
            name="bad-dep",
            steps=[WorkflowStep(name="s1", action="simulate", depends_on=["missing"])],
            circuit=CircuitPayload(qasm=QASM, shots=100),
        )
        errors = validate_workflow(defn)
        assert any("unknown step" in e for e in errors)


class TestTopologicalSort:
    def test_linear_chain(self) -> None:
        steps = [
            WorkflowStep(name="a", action="simulate"),
            WorkflowStep(name="b", action="optimise", depends_on=["a"]),
            WorkflowStep(name="c", action="hardware_run", depends_on=["b"]),
        ]
        order = topological_sort(steps)
        names = [s.name for s in order]
        assert names.index("a") < names.index("b") < names.index("c")

    def test_no_dependencies(self) -> None:
        steps = [
            WorkflowStep(name="x", action="simulate"),
            WorkflowStep(name="y", action="optimise"),
        ]
        order = topological_sort(steps)
        assert len(order) == 2

    def test_diamond_dependency(self) -> None:
        steps = [
            WorkflowStep(name="a", action="simulate"),
            WorkflowStep(name="b", action="optimise", depends_on=["a"]),
            WorkflowStep(name="c", action="benchmark", depends_on=["a"]),
            WorkflowStep(name="d", action="compare", depends_on=["b", "c"]),
        ]
        order = topological_sort(steps)
        names = [s.name for s in order]
        assert names.index("a") < names.index("b")
        assert names.index("a") < names.index("c")
        assert names.index("b") < names.index("d")
        assert names.index("c") < names.index("d")


class TestKnownActions:
    def test_expected_actions_present(self) -> None:
        assert "simulate" in KNOWN_ACTIONS
        assert "optimise" in KNOWN_ACTIONS
        assert "hardware_run" in KNOWN_ACTIONS
        assert "compare" in KNOWN_ACTIONS
        assert "benchmark" in KNOWN_ACTIONS
