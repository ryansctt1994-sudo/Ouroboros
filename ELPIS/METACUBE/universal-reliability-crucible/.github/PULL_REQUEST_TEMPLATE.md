# Universal Reliability Crucible: Pull Request

## Reliability Checklist
- [ ] All verification gates pass automatically
- [ ] No silent failure modes introduced
- [ ] Determinism preserved across all changes
- [ ] Context isolation maintained
- [ ] Scale tests pass (1 → 1,000,000)

## Change Description
[Describe the substrate change]

## Verification Evidence
```
make test
```
Output: [Paste output]

```
./scripts/determinism_gate.sh
```
Output: [Paste output]

## Impact Assessment
- [ ] Backward compatible
- [ ] Forward compatible
- [ ] Cross-language determinism maintained
- [ ] No novice SPOFs introduced

## Manifest Hash
`sha256: [GENERATED_BY_CI]`

---

**This PR must pass all automated gates before merging.**