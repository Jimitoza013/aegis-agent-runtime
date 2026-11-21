from aegis.agent.routing import (
    route_after_execution,
    route_after_planning,
    route_after_validation,
)


def test_route_after_validation_accepts_valid_task() -> None:
    assert route_after_validation({"task_status": "planning"}) == "plan"


def test_route_after_validation_rejects_failed_task() -> None:
    assert route_after_validation({"task_status": "failed"}) == "end"


def test_route_after_planning_routes_valid_plan() -> None:
    assert route_after_planning({"task_status": "running", "plan": ["Step 1"]}) == "execute"


def test_route_after_planning_stops_empty_plan() -> None:
    assert route_after_planning({"task_status": "running", "plan": []}) == "end"


def test_route_after_execution_continues_running_task() -> None:
    assert route_after_execution({"task_status": "running"}) == "execute"


def test_route_after_execution_finalizes_completed_task() -> None:
    assert route_after_execution({"task_status": "completed"}) == "finalize"


def test_route_after_execution_stops_failed_task() -> None:
    assert route_after_execution({"task_status": "failed"}) == "end"
