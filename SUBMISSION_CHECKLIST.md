# Submission Checklist

| Item | Status | Evidence |
| --- | --- | --- |
| Docker builds | PASS | `docker compose up --build -d`. |
| API starts | PASS | `/health` responds through port `8000`. |
| Tests pass | PASS | 15 deterministic pytest tests. |
| Coverage >= 85% | PASS | Audited coverage is 93.15%. |
| Required API endpoints | PASS | Metrics, funnel, heatmap, anomalies, health, ingest. |
| Dashboard works | PASS | Root page polls live metrics. |
| Detection events validate | PASS | Generated JSONL validates against `StoreEvent`. |
| Event IDs unique | PASS | UUID generation and schema validation. |
| POS correlation | PASS | Idempotent abandonment utility. |
| `DESIGN.md` complete | PASS | Expanded architecture and AI reasoning. |
| `CHOICES.md` complete | PASS | Expanded tradeoff analysis. |
| README complete | PASS | Setup, workflow, API, assumptions, troubleshooting. |
| Demo ready | PASS | `DEMO_GUIDE.md` and `DEMO_SCRIPT.md`. |
| Interview prep | PASS | `INTERVIEW_PREP.md`. |
| Push to private Git remote | PENDING USER ACTION | Requires the candidate's hosting credentials and reviewer invite. |

## Final Estimate

Estimated score: **88/100**, with the largest remaining uncertainty in held-out CV accuracy due to missing official calibration assets.

## Remaining Risks

- Replace inferred layout coordinates if the official layout arrives.
- Run a labelled count comparison before submission if ground truth becomes available.
- Add real POS records to demonstrate non-zero conversion in the live dashboard.
