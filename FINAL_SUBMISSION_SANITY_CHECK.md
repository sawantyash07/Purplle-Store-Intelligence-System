# Final Submission Sanity Check

## Scope

This audit covers submission quality only: documentation consistency, links,
filenames, evaluator instructions, packaging, and Git hygiene. It does not
change or evaluate business logic.

Audit date: 2026-05-30

## Result

**RESOLVED**

The repository is operational and the identified documentation issues were
resolved during the final repository hygiene pass.

## Documentation Inconsistencies Found

| File | Finding | Exact fix required |
|---|---|---|
| `CROSS_CAMERA_REID_FEASIBILITY.md` | Stale test-count sentence | RESOLVED: now states that the 16-test suite passes. |
| `PIPELINE_REPORT.md` | Imprecise timestamp-ordering explanation | RESOLVED: now records the verified lexical ISO sorting root cause. |
| `INTERVIEW_PREP.md` | Deleted tracked file and stale conversion-drop wording | RESOLVED: file restored and wording aligned with implementation. |
| `FINAL_ACCEPTANCE_AUDIT.md` | Older strict-compliance verdict could be mistaken for the current readiness verdict | RESOLVED: marked as historical and linked to `FINAL_SUBMISSION_REASSESSMENT.md`. |

## Broken References Found

No broken Markdown hyperlinks were found.

Validation results:

```text
broken_markdown_links=0
missing_backtick_md_refs=2
```

These two missing references were observed before `INTERVIEW_PREP.md` was
restored:

| File | Reference | Assessment |
|---|---|---|
| `SUBMISSION_CHECKLIST.md` | `INTERVIEW_PREP.md` | RESOLVED: restored. |
| `FINAL_SUBMISSION_SANITY_CHECK.md` | `INTERVIEW_PREP.md` | RESOLVED: restored. |

The following referenced inputs are intentionally absent and are already
documented as omitted challenge assets:

- `store_layout.json` from the official extraction
- populated `pos_transactions.csv`
- `sample_events.jsonl`
- `assertions.py`

The repository includes `config/store_layout.json` and
`data/pos_transactions.csv` as runnable defaults.

## Root Documentation Check

| Entry point | Result | Evidence |
|---|---|---|
| `DESIGN.md` | PASS | Root reference resolves to `docs/DESIGN.md` |
| `CHOICES.md` | PASS | Root reference resolves to `docs/CHOICES.md` |
| `docs/DESIGN.md` | PASS | Canonical design document exists |
| `docs/CHOICES.md` | PASS | Canonical choices document exists |

## README Check

The README commands are valid in the current repository location and match the
verified execution flow:

```powershell
cd "D:\Purplle Store Intelligence System"
docker compose up --build -d
curl.exe http://localhost:8000/health
python -m pipeline.replay --events data/events.jsonl --shift-to-now --batch-size 50 --delay 0
```

The earlier extraction-path portability issue was resolved:

| Finding | Exact fix required |
|---|---|
| README examples previously hard-coded the audited machine path. | RESOLVED: reviewer commands now use `<repository-path>`, while the CCTV folder remains explicit. |

## Packaging Issues Found

Tracked `INTERVIEW_PREP.md` was restored and remains referenced by
`SUBMISSION_CHECKLIST.md`.

The following submission files are currently untracked and must be included in
the final commit:

```text
ARCHITECTURE_DECISIONS.md
CHOICES.md
CROSS_CAMERA_REID_FEASIBILITY.md
DESIGN.md
EVALUATOR_SCORECARD.md
EXECUTIVE_SUMMARY.md
FINAL_ACCEPTANCE_AUDIT.md
FINAL_SUBMISSION_REASSESSMENT.md
FINAL_SUBMISSION_SANITY_CHECK.md
LIMITATIONS.md
RESULTS.md
STAFF_CLASSIFICATION_REVIEW.md
TIMESTAMP_ORDERING_ANALYSIS.md
```

The verified timestamp fix and regression test are modified tracked files and
must also be included:

```text
pipeline/correlate_pos.py
pipeline/run_all.py
tests/test_pipeline.py
```

Other modified documentation files shown by `git status` should be reviewed
and included together so the final commit is internally consistent.

## Git-Ignore Recommendations

No `.gitignore` changes are required.

The current rules correctly exclude:

```text
.coverage
.pytest_cache/
__pycache__/
data/*.db
data/*.jsonl
data/*.jpg
*.pt
CCTV Footage/
```

No generated artifacts, model weights, footage files, SQLite databases,
coverage files, or Python caches are currently tracked.

## Verified Current Numbers

| Signal | Current value |
|---|---:|
| Tests passed | 16 |
| Statement coverage | 93.15% |
| Canonical events | 326 |
| Duplicate event IDs | 0 |
| Timestamp inversions | 0 |
| Root design reference | Present |
| Root choices reference | Present |

## Final Checklist

| Item | Status |
|---|---|
| Markdown hyperlinks resolve | PASS |
| Missing backticked file references | PASS |
| Root design and choices references resolve | PASS |
| Current test and coverage numbers used by primary reports | PASS |
| Timestamp fix documented accurately everywhere | PASS |
| Report verdicts are evaluator-clear | PASS |
| README works on audited machine | PASS |
| README extraction-path portability | PASS |
| Generated artifacts excluded from Git | PASS |
| New submission documents included in final commit | PENDING |

## Submission Readiness

The identified documentation inconsistencies are resolved. See
`FINAL_REPOSITORY_HYGIENE_REPORT.md` for the final repository hygiene result.
