#!/usr/bin/env python3
import os
import sys
import yaml

def tally_votes(proposal_id):
    prop_file = f"proposals/{proposal_id}/proposal.yml"
    vote_dir  = f"proposals/{proposal_id}/votes"

    if not os.path.isfile(prop_file):
        print(f"Proposal {proposal_id} not found.")
        return

    with open(prop_file) as f:
        prop = yaml.safe_load(f)

    options = prop.get("options", [])
    results = {opt: 0 for opt in options}
    seen_users = set()

    if not os.path.isdir(vote_dir):
        print("No votes directory.")
        return

    for fname in os.listdir(vote_dir):
        if not fname.endswith(('.yml', '.yaml')):
            continue
        with open(os.path.join(vote_dir, fname)) as f:
            vote = yaml.safe_load(f)
        user = vote.get("user")
        choice = vote.get("vote")
        if not user or not choice:
            continue
        if user in seen_users:
            print(f"Duplicate vote ignored from {user}")
            continue
        if choice not in results:
            print(f"Invalid vote '{choice}' from {user}")
            continue
        seen_users.add(user)
        results[choice] += 1

    return results

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/tally_votes.py <proposal_id>")
        sys.exit(1)
    pid = sys.argv[1]
    res = tally_votes(pid)
    if res:
        print(f"\nProposal {pid} — {res.get('title', '')}\n")
        total = sum(res.values())
        for opt, cnt in res.items():
            print(f"  {opt.upper()}: {cnt}")
        print(f"\nTotal votes: {total}")
