from heavyforge.authority import calculate_authority_level
from heavyforge.contracts import JudgeDecision, WorkerOutput
from heavyforge.enums import AuthorityLevel, FailureType


def clean_worker(name: str = "direct_solver") -> WorkerOutput:
    return WorkerOutput(agent_name=name, answer="ok", confidence=0.8)


def clean_judge() -> JudgeDecision:
    return JudgeDecision(
        consensus=["ok"],
        unresolved_disputes=[],
        missing_evidence=[],
        strongest_answer="valid synthesis",
        judge_confidence=0.9,
        evidence_notes=["evidence present"],
        judge_warnings=[],
    )


def test_worker_failure_forces_draft():
    worker = WorkerOutput(
        agent_name="builder",
        failed=True,
        failure_type=FailureType.TIMEOUT,
        error_msg="timeout",
    )

    level = calculate_authority_level(
        worker_results=[worker],
        judge_decision=clean_judge(),
        judge_failed=False,
        judge_repaired=False,
    )

    assert level == AuthorityLevel.DRAFT


def test_judge_repair_forces_draft():
    level = calculate_authority_level(
        worker_results=[clean_worker()],
        judge_decision=clean_judge(),
        judge_failed=False,
        judge_repaired=True,
    )

    assert level == AuthorityLevel.DRAFT


def test_worker_repair_caps_at_plausible():
    worker = clean_worker()
    worker.repaired = True

    level = calculate_authority_level(
        worker_results=[worker],
        judge_decision=clean_judge(),
        judge_failed=False,
        judge_repaired=False,
        replay_verified=True,
    )

    assert level == AuthorityLevel.PLAUSIBLE


def test_unresolved_dispute_caps_at_plausible():
    judge = clean_judge()
    judge.unresolved_disputes = ["conflict remains"]

    level = calculate_authority_level(
        worker_results=[clean_worker()],
        judge_decision=judge,
        judge_failed=False,
        judge_repaired=False,
        replay_verified=True,
    )

    assert level == AuthorityLevel.PLAUSIBLE


def test_missing_evidence_caps_at_plausible():
    judge = clean_judge()
    judge.missing_evidence = ["missing citation"]

    level = calculate_authority_level(
        worker_results=[clean_worker()],
        judge_decision=judge,
        judge_failed=False,
        judge_repaired=False,
        replay_verified=True,
    )

    assert level == AuthorityLevel.PLAUSIBLE


def test_clean_evidence_supported_run():
    level = calculate_authority_level(
        worker_results=[clean_worker()],
        judge_decision=clean_judge(),
        judge_failed=False,
        judge_repaired=False,
    )

    assert level == AuthorityLevel.EVIDENCE_SUPPORTED


def test_replay_verified_requires_external_replay_flag():
    without_replay = calculate_authority_level(
        worker_results=[clean_worker()],
        judge_decision=clean_judge(),
        judge_failed=False,
        judge_repaired=False,
        replay_verified=False,
    )
    with_replay = calculate_authority_level(
        worker_results=[clean_worker()],
        judge_decision=clean_judge(),
        judge_failed=False,
        judge_repaired=False,
        replay_verified=True,
    )

    assert without_replay == AuthorityLevel.EVIDENCE_SUPPORTED
    assert with_replay == AuthorityLevel.REPLAY_VERIFIED
