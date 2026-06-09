# SymCrucible v0.2 Replication Kit

This document describes the E4-oriented replication path for `SYMCRUCIBLE_TRANSITION_CONSOLE_v0.2`.

## Evidence status

```text
Artifact: SYMCRUCIBLE_TRANSITION_CONSOLE_v0.2
Repository: ryansctt1994-sudo/Ouroboros
Upstream anchor commit: 88a8ce0b3346b7422ef417f024db5f45ccae9f5c
Current status: E3+ externally archived and GitHub-addressable
Not claimed: E4 independent second-party replication
Authority: TIER_UI / AUTHORITY_WEIGHT_0
```

## What the kit adds

The replication kit adds three root files:

```text
run.sh
MANIFEST.sha256
REPLICATION_RECEIPT_TEMPLATE.md
```

`run.sh` verifies required files, checks the upstream Git blob anchors listed in `MANIFEST.sha256`, emits a local `REPLICATION_OBSERVED.sha256`, and serves the console at `http://localhost:8000/`.

`MANIFEST.sha256` binds the v0.2 artifact files to the Git blob object IDs observed at the upstream anchor commit.

`REPLICATION_RECEIPT_TEMPLATE.md` gives a second party a structured attestation form.

## Replication command

```bash
git clone https://github.com/ryansctt1994-sudo/Ouroboros.git
cd Ouroboros
bash run.sh
```

## Expected outcome

A successful run should:

1. verify the required artifact files exist,
2. verify upstream blob anchors from the manifest,
3. write `REPLICATION_OBSERVED.sha256`,
4. serve the console locally,
5. allow a second party to run the UI checks and fill out `REPLICATION_RECEIPT_TEMPLATE.md`.

## Boundary

A successful `run.sh` execution is not, by itself, E4. E4 requires an independent second party to run the kit, preserve their observed manifest, and sign or otherwise attest to the replication receipt.
