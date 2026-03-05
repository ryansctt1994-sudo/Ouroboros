#!/bin/bash
# ============================================================================
# EDEN-ECS v2.0 — Finalized Test Pipeline
# ============================================================================
#
# Automates:
#   1. Rust core tests  (spatial grid, diffusion system, Weaver integration)
#   2. Python test suites (component and system tests, Weaver policies)
#   3. Unreal Engine 5 integration smoke test (if UE5 CLI is present)
#
# Exit codes:
#   0 — all suites passed
#   1 — one or more suites failed
#
# Usage:
#   ./run_all_tests.sh              # Run all suites
#   ./run_all_tests.sh --rust-only  # Rust tests only (fast CI path)
#   SKIP_UE5=1 ./run_all_tests.sh  # Skip UE5 smoke test
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ── Flags ─────────────────────────────────────────────────────────────────────
RUST_ONLY=0
SKIP_UE5="${SKIP_UE5:-0}"
for arg in "$@"; do
    case "$arg" in
        --rust-only) RUST_ONLY=1 ;;
    esac
done

# ── Helpers ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Colour

passed=0
failed=0
skipped=0

log_header() { echo -e "\n${CYAN}══════════════════════════════════════════${NC}"; \
               echo -e "${CYAN} $1${NC}"; \
               echo -e "${CYAN}══════════════════════════════════════════${NC}"; }

run_suite() {
    local label="$1"; shift
    echo -e "\n${YELLOW}▶ ${label}${NC}"
    if "$@" > /tmp/eden_test_output.txt 2>&1; then
        echo -e "${GREEN}  ✅ PASS${NC}"
        passed=$((passed + 1))
    else
        echo -e "${RED}  ❌ FAIL${NC}"
        cat /tmp/eden_test_output.txt
        failed=$((failed + 1))
    fi
}

run_python_test() {
    local file="$1"
    echo -e "\n${YELLOW}▶ ${file}${NC}"
    if python "${file}" > /tmp/eden_test_output.txt 2>&1; then
        grep -E "(✅|passing|PASS|ok)" /tmp/eden_test_output.txt | tail -3 || true
        echo -e "${GREEN}  ✅ PASS${NC}"
        passed=$((passed + 1))
    else
        cat /tmp/eden_test_output.txt
        echo -e "${RED}  ❌ FAIL${NC}"
        failed=$((failed + 1))
    fi
}

skip_suite() {
    local label="$1"
    echo -e "\n${YELLOW}▶ ${label}${NC}"
    echo -e "  ⏭  SKIPPED (not available in this environment)"
    skipped=$((skipped + 1))
}

# ── 1. Rust core tests ─────────────────────────────────────────────────────────
log_header "1/3  Rust Core Tests"

MANIFEST="${SCRIPT_DIR}/Cargo.toml"

run_suite "Rust unit tests (spatial_grid, diffusion, weaver, telemetry_ffi, tracy)" \
    cargo test --manifest-path "${MANIFEST}" --lib

run_suite "Rust doc-tests" \
    cargo test --manifest-path "${MANIFEST}" --doc

# ── 2. Python test suites ──────────────────────────────────────────────────────
if [ "${RUST_ONLY}" -eq 1 ]; then
    log_header "2/3  Python Tests  [SKIPPED — --rust-only]"
    skipped=$((skipped + 1))
else
    log_header "2/3  Python Tests"

    cd "${SCRIPT_DIR}"

    # Core component tests
    for f in test_core.py test_timestep.py test_loyalty_enhanced.py \
              test_quantum.py test_memory.py test_balance_system.py \
              test_new_components.py test_metacube.py; do
        [ -f "${f}" ] && run_python_test "${f}" || true
    done

    # Sub-directory system tests
    for f in tests/test_coherence_accumulator.py \
              tests/test_palindrome.py \
              tests/test_ternary_register.py \
              tests/test_veto_system.py; do
        [ -f "${f}" ] && run_python_test "${f}" || true
    done

    # Weaver policy tests (Python-side validation)
    if [ -f "tests/test_weaver_policies.py" ]; then
        run_python_test "tests/test_weaver_policies.py"
    fi

    cd "${REPO_ROOT}"
fi

# ── 3. Unreal Engine 5 smoke test ─────────────────────────────────────────────
log_header "3/3  Unreal Engine 5 Integration Smoke Test"

if [ "${SKIP_UE5}" -eq 1 ]; then
    skip_suite "UE5 smoke test (SKIP_UE5=1)"
elif command -v UnrealEditor-Cmd > /dev/null 2>&1; then
    UE5_PROJECT="${REPO_ROOT}/ue/EdenECS.uproject"
    if [ -f "${UE5_PROJECT}" ]; then
        run_suite "UE5 Niagara/FFI smoke test" \
            UnrealEditor-Cmd "${UE5_PROJECT}" \
                -ExecCmds="Automation RunTests EdenECS.SmokeTest; Quit" \
                -Unattended -NullRHI -log
    else
        skip_suite "UE5 project not found at ${UE5_PROJECT}"
    fi
else
    skip_suite "UnrealEditor-Cmd not found in PATH"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
log_header "Test Summary"

total=$((passed + failed + skipped))
echo "  Passed:  ${passed}"
echo "  Failed:  ${failed}"
echo "  Skipped: ${skipped}"
echo "  Total:   ${total}"
echo ""

if [ "${failed}" -eq 0 ]; then
    echo -e "${GREEN}🎉 All executed suites passed!${NC}"
    exit 0
else
    echo -e "${RED}⚠️  ${failed} suite(s) failed.${NC}"
    exit 1
fi

