# Detection Evaluation

## Strengths

- YOLO11 nano is practical for CPU evaluation and retains confidence.
- Bottom-centre trajectories are robust to torso occlusion.
- Individual tracker IDs preserve group entry counting when detector recall is adequate.
- Threshold debounce permits exit and re-entry on a surviving track.
- Idle pruning closes zones after disappearance.
- Queue depth counts only people inside the billing rectangle.
- Output sorting gives globally chronological JSONL across camera clips.

## Weaknesses

- No labelled ground truth was included for precision, recall, or count-error measurement.
- Doorway Re-ID is geometric and can confuse different people returning through a similar path.
- Cross-camera identity is intentionally not guessed.
- Long continuous presence is only a staff proxy.

## Known Edge Cases

| Edge Case | Handling |
| --- | --- |
| Group entry | Each detector track can emit its own threshold event. |
| Partial occlusion | Low confidence is retained; disappeared zones close after timeout. |
| Re-entry | Recent exit token reused near the same doorway. |
| Empty periods | No events emitted; API remains stable. |
| Billing buildup | Region-scoped depth emitted with queue joins. |
| Camera overlap | Entrance sessions are authoritative; floor IDs do not inflate funnels. |

## Expected Performance

API schema correctness is high and mechanically validated. Detection accuracy is expected to be reasonable for visible people in `CAM 1`, `CAM 2`, and `CAM 3`, with lower recall in the heavily occluded additional floor view. The next accuracy improvement should be labelled evaluation, then zone calibration and model-size comparison.

