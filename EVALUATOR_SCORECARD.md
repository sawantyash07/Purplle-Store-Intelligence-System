# Evaluator Scorecard

## Estimated Score

**70 / 100** base score, with an eligible dashboard bonus.

This estimate is intentionally conservative. API correctness, production readiness, AI engineering documentation, and the dashboard are strongly evidenced. The largest uncertainty is computer-vision accuracy because official ground truth and calibration assets were unavailable.

| Rubric Area | Maximum | Expected | Reasoning | Evidence |
| --- | ---: | ---: | --- | --- |
| Detection and event generation | 30 | 15 | The pipeline and schema work, but ground-truth accuracy is unverified, cross-camera deduplication is absent, and staff classification is not demonstrated by the clips. | `PIPELINE_REPORT.md`, `EVENT_VALIDATION.md`, `STAFF_CLASSIFICATION_REVIEW.md` |
| Intelligence API | 35 | 22 | Required endpoints, heatmap, anomalies, health, and ingest work. The canonical funnel materially under-reports downstream stages. | `API_TEST_REPORT.md`, `RESULTS.md`, `CROSS_CAMERA_REID_FEASIBILITY.md` |
| Production readiness | 20 | 19 | Compose, logging, graceful degradation, tests, and coverage are strong. | `SYSTEM_VERIFICATION_REPORT.md`, `TEST_REPORT.md` |
| AI-assisted engineering evidence | 15 | 14 | Decisions, rejected suggestions, prompts, and tradeoffs are documented. | `docs/DESIGN.md`, `docs/CHOICES.md`, test headers |
| **Base score** | **100** | **70** | Strict estimate aligned with the final acceptance audit. | `FINAL_ACCEPTANCE_AUDIT.md` |
| Connected dashboard bonus | +10 | +8 | Live dashboard polls metrics and browser validation found visible metrics with no console errors. | `DASHBOARD_REPORT.md`, `DEMO_GUIDE.md` |

## Normalized Submission Estimate

To avoid overstating the bonus and unresolved held-out CV uncertainty, the recommended headline estimate is **70/100** base score. The connected dashboard remains eligible for bonus consideration.

## Evaluator Notes

- Start with `README.md` and `EXECUTIVE_SUMMARY.md`.
- Use `RESULTS.md` for measured outputs.
- Use `SYSTEM_VERIFICATION_REPORT.md` for full end-to-end evidence.
- Use `CROSS_CAMERA_REID_FEASIBILITY.md` for the documented funnel limitation and safety decision.
