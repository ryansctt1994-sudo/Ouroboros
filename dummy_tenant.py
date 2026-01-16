#!/usr/bin/env python3
import json
import os
import sys
import time
from pathlib import Path

REQUIRED_TOP_LEVEL = {
    "mandate_id": str,
    "tenant_class": str,
    "scope_boundary": list,
    "axiom_set": list,
    "compute_budget": dict,
    "resource_permissions": dict,
    "issued_at_utc": int,
    "signature": str,
}

def die(code: int, msg: str):
    report = {
        "witness_report_version": "0.1",
        "mandate_id": "UNKNOWN",
        "tenant_class": "DummyTenant",
        "status": "FAIL",
        "violations": [msg],
        "artifacts": [],
        "metrics": {"elapsed_ms": 0},
        "timestamp_utc": int(time.time()),
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    sys.exit(code)

def load_mandate(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        die(2, f"MANDATE_READ_ERROR: {e}")
    for k, t in REQUIRED_TOP_LEVEL.items():
        if k not in data:
            die(3, f"MANDATE_SCHEMA_MISSING_FIELD: {k}")
        if not isinstance(data[k], t):
            die(3, f"MANDATE_SCHEMA_TYPE_MISMATCH: {k} expected {t.__name__}")
    cb = data["compute_budget"]
    if "max_tokens" not in cb or "max_seconds" not in cb:
        die(3, "MANDATE_SCHEMA_INVALID: compute_budget missing max_tokens/max_seconds")
    rp = data["resource_permissions"]
    if "read" not in rp or "write" not in rp:
        die(3, "MANDATE_SCHEMA_INVALID: resource_permissions missing read/write")
    return data

def ensure_scope(scope_boundary):
    for p in scope_boundary:
        if not isinstance(p, str) or not p.startswith("/"):
            die(4, f"SCOPE_INVALID_PATH: {p}")
    return True

def main():
    start = time.time()
    if len(sys.argv) != 2:
        die(1, "USAGE: dummy_tenant.py /path/to/genesis_mandate.json")
    mandate_path = Path(sys.argv[1])
    mandate = load_mandate(mandate_path)
    ensure_scope(mandate["scope_boundary"])
    time.sleep(0.05)
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    log_path = logs_dir / "genesis.log"
    log_path.write_text(f"[{int(time.time())}] DummyTenant ok for {mandate['mandate_id']}\n", encoding="utf-8")
    elapsed_ms = int((time.time() - start) * 1000)
    report = {
        "witness_report_version": "0.1",
        "mandate_id": mandate["mandate_id"],
        "tenant_class": mandate["tenant_class"],
        "status": "OK",
        "violations": [],
        "artifacts": [{"type": "log", "path": str(log_path.resolve())}],
        "metrics": {
            "elapsed_ms": elapsed_ms,
            "declared_max_seconds": mandate["compute_budget"]["max_seconds"],
            "declared_max_tokens": mandate["compute_budget"]["max_tokens"],
        },
        "timestamp_utc": int(time.time()),
        "notes": "Signature verification intentionally stubbed in DummyTenant.",
    }
    print(json.dumps(report, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
