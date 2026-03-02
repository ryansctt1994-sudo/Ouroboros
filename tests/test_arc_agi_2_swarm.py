"""
Tests for the arc_agi_2_swarm package.

Covers:
- dsl_primitives: identity, rotate_grid, flip_grid, apply_symmetry,
  recolor, fill_region, extract_objects
- evolutionary_swarm: Candidate, EvolutionarySwarm (init, evolve, mutate,
  crossover)
- fitness_evaluator: FitnessEvaluator (exact-match, MDL, composite score)
- repl_agent_scaffold: ReplAgentScaffold (run loop, execute_code)
- abstraction_library_seed.json: schema validation
"""

import json
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from arc_agi_2_swarm.dsl_primitives import (
    apply_symmetry,
    extract_objects,
    fill_region,
    flip_grid,
    identity,
    recolor,
    rotate_grid,
)
from arc_agi_2_swarm.evolutionary_swarm import Candidate, EvolutionarySwarm
from arc_agi_2_swarm.fitness_evaluator import FitnessEvaluator, FitnessScore
from arc_agi_2_swarm.repl_agent_scaffold import ReplAgentScaffold, ReplSession


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def simple_grid():
    return np.array([[1, 2], [3, 4]], dtype=np.int32)


@pytest.fixture()
def training_pairs(simple_grid):
    """One trivial training pair where the target equals the input."""
    return [(simple_grid.copy(), simple_grid.copy())]


@pytest.fixture()
def evaluator(training_pairs):
    return FitnessEvaluator(training_pairs)


# ---------------------------------------------------------------------------
# dsl_primitives
# ---------------------------------------------------------------------------

class TestDslPrimitives:
    def test_identity_returns_copy(self, simple_grid):
        result = identity(simple_grid)
        assert np.array_equal(result, simple_grid)

    def test_identity_is_copy(self, simple_grid):
        result = identity(simple_grid)
        result[0, 0] = 99
        assert simple_grid[0, 0] == 1  # original unchanged

    def test_rotate_grid_k1(self, simple_grid):
        rotated = rotate_grid(simple_grid, k=1)
        expected = np.rot90(simple_grid, k=1)
        assert np.array_equal(rotated, expected)

    def test_rotate_grid_k2(self, simple_grid):
        rotated = rotate_grid(simple_grid, k=2)
        expected = np.rot90(simple_grid, k=2)
        assert np.array_equal(rotated, expected)

    def test_rotate_grid_k0_is_identity(self, simple_grid):
        assert np.array_equal(rotate_grid(simple_grid, k=0), simple_grid)

    def test_flip_axis0(self, simple_grid):
        flipped = flip_grid(simple_grid, axis=0)
        expected = np.flip(simple_grid, axis=0)
        assert np.array_equal(flipped, expected)

    def test_flip_axis1(self, simple_grid):
        flipped = flip_grid(simple_grid, axis=1)
        expected = np.flip(simple_grid, axis=1)
        assert np.array_equal(flipped, expected)

    def test_apply_symmetry_diagonal(self, simple_grid):
        result = apply_symmetry(simple_grid, kind="diagonal")
        assert np.array_equal(result, simple_grid.T)

    def test_apply_symmetry_unknown_raises(self, simple_grid):
        with pytest.raises(ValueError, match="Unknown symmetry kind"):
            apply_symmetry(simple_grid, kind="invalid")

    def test_recolor_basic(self, simple_grid):
        result = recolor(simple_grid, {1: 9})
        assert result[0, 0] == 9
        assert result[0, 1] == 2  # unchanged

    def test_recolor_no_op(self, simple_grid):
        result = recolor(simple_grid, {99: 0})
        assert np.array_equal(result, simple_grid)

    def test_fill_region_basic(self):
        grid = np.zeros((3, 3), dtype=np.int32)
        grid[1, 1] = 1  # obstacle
        result = fill_region(grid, row=0, col=0, fill_color=5, target_color=0)
        # All zeros except (1,1) which is 1 should remain
        assert result[0, 0] == 5
        assert result[1, 1] == 1  # untouched

    def test_fill_region_out_of_bounds(self, simple_grid):
        result = fill_region(simple_grid, row=99, col=99, fill_color=0)
        assert np.array_equal(result, simple_grid)

    def test_extract_objects_single(self):
        grid = np.zeros((4, 4), dtype=np.int32)
        grid[1:3, 1:3] = 2
        objects = extract_objects(grid, background=0)
        assert len(objects) == 1
        assert objects[0]["color"] == 2
        assert len(objects[0]["pixels"]) == 4

    def test_extract_objects_empty_grid(self):
        grid = np.zeros((3, 3), dtype=np.int32)
        objects = extract_objects(grid, background=0)
        assert objects == []

    def test_extract_objects_bbox(self):
        grid = np.zeros((5, 5), dtype=np.int32)
        grid[2, 2] = 3
        objects = extract_objects(grid)
        assert len(objects) == 1
        r_min, c_min, r_max, c_max = objects[0]["bbox"]
        assert (r_min, c_min, r_max, c_max) == (2, 2, 2, 2)


# ---------------------------------------------------------------------------
# evolutionary_swarm
# ---------------------------------------------------------------------------

class TestCandidate:
    def test_defaults(self):
        c = Candidate()
        assert c.program_id
        assert c.dsl_ops == []
        assert c.fitness is None
        assert c.generation == 0

    def test_fingerprint_stable(self):
        c = Candidate(dsl_ops=[{"op": "identity", "args": {}}])
        assert c.fingerprint() == c.fingerprint()

    def test_fingerprint_differs(self):
        c1 = Candidate(dsl_ops=[{"op": "identity", "args": {}}])
        c2 = Candidate(dsl_ops=[{"op": "rotate_grid", "args": {}}])
        assert c1.fingerprint() != c2.fingerprint()


class TestEvolutionarySwarm:
    def test_init_population_size(self):
        swarm = EvolutionarySwarm(population_size=10)
        assert len(swarm.population) == 10

    def test_init_with_seeds(self):
        seeds = [Candidate() for _ in range(3)]
        swarm = EvolutionarySwarm(population_size=5, seed_candidates=seeds)
        assert len(swarm.population) == 5

    def test_invalid_elite_fraction(self):
        with pytest.raises(ValueError):
            EvolutionarySwarm(elite_fraction=0.0)

    def test_invalid_mutation_rate(self):
        with pytest.raises(ValueError):
            EvolutionarySwarm(mutation_rate=1.5)

    def test_evolve_returns_candidate(self):
        swarm = EvolutionarySwarm(population_size=5, rng_seed=42)

        def dummy_fitness(c):
            return len(c.dsl_ops) * 0.1

        best = swarm.evolve(dummy_fitness, num_generations=3)
        assert isinstance(best, Candidate)

    def test_best_candidate_none_when_no_scores(self):
        swarm = EvolutionarySwarm(population_size=3)
        # All candidates start with fitness=None
        result = swarm.best_candidate()
        assert result is None

    def test_mutation_produces_different_id(self):
        swarm = EvolutionarySwarm(population_size=5, rng_seed=0)
        parent = Candidate(dsl_ops=[{"op": "identity", "args": {}}])
        child = swarm._mutate(parent)
        assert child.program_id != parent.program_id
        assert child.fitness is None

    def test_crossover_inherits_parent_ids(self):
        swarm = EvolutionarySwarm(population_size=5, rng_seed=0)
        p1 = Candidate(dsl_ops=[{"op": "identity", "args": {}}])
        p2 = Candidate(dsl_ops=[{"op": "rotate_grid", "args": {}}])
        child = swarm._crossover(p1, p2)
        assert p1.program_id in child.parent_ids
        assert p2.program_id in child.parent_ids


# ---------------------------------------------------------------------------
# fitness_evaluator
# ---------------------------------------------------------------------------

class TestFitnessEvaluator:
    def test_empty_pairs_raises(self):
        with pytest.raises(ValueError, match="training_pairs must not be empty"):
            FitnessEvaluator([])

    def test_exact_match_identity(self, evaluator):
        """Identity program should score exact_match=1.0."""
        c = Candidate(dsl_ops=[{"op": "identity", "args": {}}])
        score = evaluator.evaluate(c)
        assert score.exact_match == pytest.approx(1.0)
        assert score.total > 0

    def test_exact_match_wrong(self, training_pairs):
        """Recoloring program that changes values should fail exact match."""
        inp = np.array([[1, 2], [3, 4]], dtype=np.int32)
        tgt = np.array([[1, 2], [3, 4]], dtype=np.int32)
        ev = FitnessEvaluator([(inp, tgt)])
        c = Candidate(dsl_ops=[{"op": "recolor", "args": {"color_map": {1: 9}}}])
        score = ev.evaluate(c)
        assert score.exact_match < 1.0

    def test_mdl_penalty_positive(self, evaluator):
        c = Candidate(dsl_ops=[{"op": "identity", "args": {}}])
        score = evaluator.evaluate(c)
        assert score.mdl_penalty >= 0

    def test_kl_bonus_non_negative(self, evaluator):
        c = Candidate(dsl_ops=[{"op": "identity", "args": {}}])
        score = evaluator.evaluate(c)
        assert score.kl_bonus >= 0

    def test_callable_interface(self, evaluator):
        """FitnessEvaluator is callable and returns a float."""
        c = Candidate(dsl_ops=[{"op": "identity", "args": {}}])
        result = evaluator(c)
        assert isinstance(result, float)

    def test_details_length(self, training_pairs):
        pairs = [(np.zeros((2, 2), dtype=np.int32), np.zeros((2, 2), dtype=np.int32))]
        ev = FitnessEvaluator(pairs)
        c = Candidate()
        score = ev.evaluate(c)
        assert len(score.details) == len(pairs)


# ---------------------------------------------------------------------------
# repl_agent_scaffold
# ---------------------------------------------------------------------------

class TestReplAgentScaffold:
    @pytest.fixture()
    def scaffold(self, training_pairs):
        ev = FitnessEvaluator(training_pairs)
        return ReplAgentScaffold(fitness_evaluator=ev, max_steps=3)

    def test_run_returns_session(self, scaffold):
        session = scaffold.run(initial_code="")
        assert isinstance(session, ReplSession)

    def test_run_records_history(self, scaffold):
        session = scaffold.run(initial_code="")
        assert len(session.history) >= 1

    def test_execute_code_valid(self, scaffold):
        code = "def solve(grid):\n    return grid\n"
        inp = np.array([[1, 2], [3, 4]], dtype=np.int32)
        out, err = scaffold.execute_code(code, inp)
        assert err is None
        assert np.array_equal(out, inp)

    def test_execute_code_no_solve_fn(self, scaffold):
        code = "x = 1\n"
        inp = np.zeros((2, 2), dtype=np.int32)
        out, err = scaffold.execute_code(code, inp)
        assert out is None
        assert "solve" in err

    def test_execute_code_syntax_error(self, scaffold):
        code = "def solve(\n"
        inp = np.zeros((2, 2), dtype=np.int32)
        out, err = scaffold.execute_code(code, inp)
        assert out is None
        assert err is not None

    def test_best_score_updated(self, scaffold):
        session = scaffold.run(
            initial_dsl_ops=[{"op": "identity", "args": {}}]
        )
        assert session.best_score > float("-inf")

    def test_session_reuse(self, scaffold):
        existing = ReplSession(session_id="test-123")
        session = scaffold.run(session=existing)
        assert session.session_id == "test-123"


# ---------------------------------------------------------------------------
# abstraction_library_seed.json
# ---------------------------------------------------------------------------

class TestAbstractionLibrarySeed:
    _SEED_PATH = os.path.join(
        os.path.dirname(__file__), "..", "arc_agi_2_swarm", "abstraction_library_seed.json"
    )

    def _load(self):
        with open(self._SEED_PATH, encoding="utf-8") as f:
            return json.load(f)

    def test_file_exists(self):
        assert os.path.isfile(self._SEED_PATH)

    def test_valid_json(self):
        data = self._load()
        assert isinstance(data, dict)

    def test_required_top_level_keys(self):
        data = self._load()
        for key in ("version", "description", "patterns"):
            assert key in data, f"Missing key: {key}"

    def test_patterns_non_empty(self):
        data = self._load()
        assert len(data["patterns"]) > 0

    def test_pattern_schema(self):
        data = self._load()
        for p in data["patterns"]:
            for key in ("id", "name", "description", "dsl_ops", "tags"):
                assert key in p, f"Pattern missing key: {key}"
            assert isinstance(p["dsl_ops"], list)
            assert isinstance(p["tags"], list)

    def test_known_patterns_present(self):
        data = self._load()
        ids = {p["id"] for p in data["patterns"]}
        for expected_id in ("identity", "mirror_horizontal", "rotate_90"):
            assert expected_id in ids, f"Missing pattern: {expected_id}"
