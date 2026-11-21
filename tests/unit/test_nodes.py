from aegis.agent.nodes import (
    create_initial_plan,
    execute_next_step,
    finalize_task,
    validate_input,
)


def test_validate_input_accepts_valid_task() -> None:
    result = validate_input({"user_input": "Research AI agents"})

    assert result["task_status"] == "planning"
    assert result["error"] is None


def test_validate_input_rejects_empty_task() -> None:
    result = validate_input({"user_input": "   "})

    assert result["task_status"] == "failed"
    assert result["error"] == "User input cannot be empty."


def test_create_initial_plan() -> None:
    result = create_initial_plan({"user_input": "Research AI agents"})

    assert len(result["plan"]) == 4
    assert result["current_step"] == 0
    assert result["iteration_count"] == 0
    assert result["task_status"] == "running"


def test_execute_next_step_advances_plan() -> None:
    result = execute_next_step(
        {
            "current_step": 0,
            "iteration_count": 0,
            "max_iterations": 5,
            "plan": ["Step 1", "Step 2"],
        }
    )

    assert result["current_step"] == 1
    assert result["iteration_count"] == 1
    assert result["task_status"] == "running"


def test_execute_next_step_completes_plan() -> None:
    result = execute_next_step(
        {
            "current_step": 1,
            "iteration_count": 1,
            "max_iterations": 5,
            "plan": ["Step 1", "Step 2"],
        }
    )

    assert result["current_step"] == 2
    assert result["task_status"] == "completed"


def test_execute_next_step_respects_iteration_limit() -> None:
    result = execute_next_step(
        {
            "current_step": 1,
            "iteration_count": 5,
            "max_iterations": 5,
            "plan": ["Step 1", "Step 2"],
        }
    )

    assert result["task_status"] == "failed"
    assert result["error"] == "Maximum iteration limit reached."


def test_finalize_task_success() -> None:
    result = finalize_task(
        {
            "user_input": "Research AI agents",
            "task_status": "running",
        }
    )

    assert result["task_status"] == "completed"
    assert result["final_response"] == ("Task completed successfully: Research AI agents")


def test_finalize_task_failure() -> None:
    result = finalize_task(
        {
            "user_input": "Research AI agents",
            "task_status": "failed",
            "error": "Execution failed.",
        }
    )

    assert result["final_response"] == "Execution failed."
