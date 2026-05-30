# Cross-Camera Re-ID Feasibility Review

## Recommendation

**NO-GO**

Do not add cross-camera Re-ID before submission.

Risk is **MEDIUM to HIGH**, not LOW. The repository is currently stable, the existing 16-test suite passes, and a safe measurable funnel improvement cannot be demonstrated from the available evidence without introducing new identity assumptions.

## Root Cause

The funnel and heatmap answer different identity questions.

`pipeline/tracker.py` creates visitor tokens independently inside each camera:

```python
def _visitor_token(camera_id: str, track_id: int, timestamp: datetime) -> str:
    seed = f"{camera_id}:{track_id}:{timestamp.isoformat()}".encode()
    return "VIS_" + hashlib.sha1(seed).hexdigest()[:8]
```

Because the camera ID is part of the token seed, the same physical person receives different visitor IDs on entrance, floor, and billing cameras.

`app/analytics.py` deliberately keeps the funnel conservative:

```python
if stages["entry"]:
    stages["zone_visit"] &= stages["entry"]
    stages["billing_queue"] &= stages["entry"]
    stages["purchase"] &= stages["entry"]
```

The measured canonical stream contains:

| Set | Unique Tokens |
| --- | ---: |
| Entry or re-entry sessions | 3 |
| Zone tokens | 105 |
| Billing tokens | 20 |
| Entry tokens also present in zone events | 0 |
| Entry tokens also present in billing events | 0 |

The funnel therefore returns `entry=3`, `zone_visit=0`, `billing_queue=0`, and `purchase=0`.

The heatmap does not require entrance linkage. It counts local zone-camera tokens directly and reports:

| Zone | Visits |
| --- | ---: |
| Billing | 20 |
| Makeup | 45 |
| Skincare | 48 |

## Expected Funnel Improvement

A correct cross-camera identity layer could link entrance sessions to later floor and billing events. The theoretical outcome is a funnel where:

```text
entry >= zone_visit >= billing_queue >= purchase
```

with non-zero zone visits when entrance customers are observed on floor cameras.

However, the supplied stream does not contain enough evidence to measure the correct linked counts. A non-zero result alone would not prove an improvement: it could be false linkage.

Measured timestamp ambiguity is substantial:

| Entrance Session | Zone-Entry Candidates Within 120 Seconds |
| --- | ---: |
| `VIS_85cb94e0` | 4 |
| `VIS_6511ed38` re-entry | 81 |
| `VIS_8b406d81` re-entry | 94 |

Timestamp-only matching would therefore inflate or misassign sessions.

## Candidate Solutions

### 1. Timestamp-Only Matching

Link the closest later zone event to an entrance session.

**Benefit:** Small implementation footprint.

**Risk:** HIGH. Crowded windows contain dozens of candidates. The method would fabricate identity and could worsen funnel accuracy while appearing numerically improved.

### 2. Timestamp Plus Camera Transition Rules

Define expected travel windows between entrance, floor, and billing cameras. Match local tokens using time proximity and route constraints.

**Benefit:** More conservative than timestamp-only matching.

**Risk:** MEDIUM to HIGH. The repository lacks calibrated transition windows, overlap polygons, labelled trajectories, and conflict-resolution rules. Crowded periods remain ambiguous.

### 3. Appearance Embeddings

Extract person crops and compare OSNet or similar embeddings across camera views.

**Benefit:** Most plausible path to actual cross-camera identity linking.

**Risk:** MEDIUM to HIGH before submission. It adds model dependencies, threshold calibration, privacy review, crop storage decisions, occlusion sensitivity, and new evaluation requirements. The supplied footage has no labelled identity ground truth.

### 4. Hybrid Track Graph

Build an offline graph using appearance similarity, timestamp windows, camera adjacency, and one-to-one assignment. Preserve confidence and leave uncertain tracks unlinked.

**Benefit:** Best production direction.

**Risk:** MEDIUM to HIGH. It requires labelled validation, calibration, and careful regression testing. It is not a low-risk last-minute patch.

### 5. Keep Conservative Funnel Semantics

Leave the current intersection logic intact and document that cross-camera Re-ID is intentionally conservative.

**Benefit:** No regression risk. Existing APIs, dashboard, schema, and tests remain unchanged.

**Risk:** Funnel under-reports downstream stages on the real multi-camera stream.

## Implementation Risk Assessment

| Requirement | Assessment |
| --- | --- |
| Risk must be LOW | **FAIL**. Any effective approach is MEDIUM or HIGH risk. |
| Existing tests remain green | Current suite passes: `16 passed`. New Re-ID behavior would need additional labelled tests. |
| APIs unchanged | Possible, but not sufficient to make the change safe. |
| Dashboard unchanged | Possible, but metrics could change materially. |
| Event schema unchanged | Possible with token rewriting or an internal alias map, but both require calibration. |
| Funnel measurably improves | Non-zero values are easy to produce, but correctness cannot be measured from available data. |

## Safe Next Step

Do not modify code before submission. Document the limitation and present the production plan:

1. Label a small cross-camera trajectory set.
2. Benchmark timestamp-only, transition-rule, and appearance-embedding linkage.
3. Add one-to-one assignment with confidence thresholds.
4. Leave uncertain tracks unlinked.
5. Compare funnel precision and recall against labelled sessions.
6. Only then introduce the identity layer behind the existing API contract.

## Final Decision

**NO-GO**

The current zero-valued downstream funnel is conservative and explainable. A rushed cross-camera Re-ID patch would make the numbers look better without proving they are more accurate, which would violate the north-star metric objective and the safety requirement.
