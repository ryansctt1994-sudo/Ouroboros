# Cathedral Governance MVP

This directory contains a minimal, replayable governance system.

## Dependencies

- Python 3
- PyYAML (`pip install pyyaml`)

## Usage

1. Add users in `users/` (one YAML file per user).
2. Create a proposal under `proposals/XXX/` with a `proposal.yml` and a `votes/` subdirectory.
3. Let users cast votes by placing YAML files in `votes/` (one per user).
4. Run `scripts/tally_votes.py <proposal_id>` to count votes.

All history is stored in plain files – anyone can audit or replay the entire governance timeline.
