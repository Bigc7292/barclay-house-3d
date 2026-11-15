# Fresh-critic loop (trick #17)

The builder never grades itself. Each round, a **new** critic that has not seen prior work (no `critic_log.md`, no earlier defects, no builder notes) scores the latest locked-camera still.

## Inputs (only these)

1. The locked-camera render (one still, same camera as the last pass).
2. The matching reference crop (from `refs/checklist_<cam>.json` / the sourced photo).
3. The `checks.py` report for that camera (`out/checklist_<cam>.md`).

Do **not** give the critic `critic_log.md` or a list of previous fixes. Taste calls that need a preference (e.g. parapet tone) are shown as two stills A/B; the critic picks one.

## Output schema

Write this block verbatim into `critic_log.md` (plus the date in Asia/Dubai, UTC+4):

```
## Critic round <N> (fresh, <date> Asia/Dubai)
Camera: <cam>   Render: <path>   Ref: <path>
checks.py: gate <PASS|FAIL> (no=<n>, partial=<n>); rows: <element=status, ...>
Verdict: yes | no

Problems (≤5, worst first). Each fix must be numeric (a value, not prose):
1. <element> — <what's wrong, citing the checks.py row if one exists>. Fix: <e.g. albedo V 0.62→0.48>.
2. ...

Already good:
- <what already matches the ref>

Taste A/B (optional): <question>. A: <path or description>. B: <path or description>. Pick: A|B. Why: <one line>.

Applied this pass: rank-1 only (trick #1). Other ranks wait.
```

- `Verdict: yes` only if you would accept the still against the ref for this camera (checklist gate is necessary but not sufficient).
- At most 5 problems. No sixth "also". If fewer than 5 are real, stop.
- A numeric fix is a quantity the builder can apply: albedo/roughness/coat, metres, pixel crop stat, sample count, exposure EV, etc. Not "darken it a bit".
- Taste (colour preference with no sourced target) is A/B, not a "problem".

## Builder rules

- Apply **only the rank-1 fix** this pass (trick #1, locked camera).
- Then re-render, re-run `python3 checks.py --cam <cam>`, and spawn a **new** fresh critic (new executor / Interior bot, empty context).
- Success for a pass: the rank-1 element's `checks.py` row moves `partial`→`yes` or `no`→`partial`/`yes`.
