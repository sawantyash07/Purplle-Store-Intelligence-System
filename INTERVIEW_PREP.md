# Interview Preparation

## Detection and Tracking

1. **Why YOLO11 nano?**  
   It is CPU-practical, current in the installed Ultralytics runtime, and easy to upgrade after labelled benchmarking.

2. **Why not YOLOv8?**  
   YOLOv8 remains valid. YOLO11 nano offered the same integration shape with the newer available family.

3. **Why not RT-DETR?**  
   Its heavier CPU cost slows iteration. I would benchmark it only if labelled recall shows YOLO11 is insufficient.

4. **Why confidence `0.18`?**  
   Retail occlusion can lower confidence. I retain uncertain detections and preserve confidence instead of silently dropping them.

5. **Why bottom-centre coordinates?**  
   They approximate a person's floor position and remain more stable when displays obscure the torso.

6. **How are groups counted?**  
   Each detected track crosses independently and can emit its own `ENTRY`.

7. **What happens when a track disappears?**  
   After three idle seconds, open zones close at the last observed timestamp.

8. **How is dwell emitted?**  
   Every 30 seconds of continuous presence, with cumulative dwell milliseconds.

9. **How is direction determined?**  
   A horizontal entrance line compares the previous and current bottom-centre Y coordinate.

10. **Why a crossing debounce?**  
    It suppresses jitter near the line while permitting a genuine later exit or return.

11. **How do you calibrate zones?**  
    Configure rectangles per camera in `config/store_layout.json`; official layout coordinates should replace inferred defaults.

12. **What did CAM 5 reveal?**  
    Heavy occlusion can reduce retained tracks. It is the first angle I would recalibrate or benchmark with a larger model.

## Re-ID and Staff

13. **How does re-entry work?**  
    A recent exit near the same door can reuse its visitor token and emit `REENTRY`.

14. **What breaks the Re-ID heuristic?**  
    Two different people using similar door positions inside five minutes can be confused.

15. **Why not claim cross-camera identity?**  
    The footage is anonymised and lacks labelled identity pairs. Unsupported guesses would inflate the funnel.

16. **How are floor-camera IDs used?**  
    They enrich heatmap and dwell analytics. Funnel stages intersect with authoritative entrance sessions.

17. **How is staff detected?**  
    A long continuously tracked presence is flagged as a conservative transparent proxy.

18. **How would you improve staff detection?**  
    Calibrate a uniform embedding classifier with consented staff images and combine it with shift context.

19. **Why reject a hosted VLM?**  
    It adds privacy, latency, and cost concerns without supplied labels proving value.

## Events and POS

20. **Why immutable events?**  
    They are replayable, auditable, and easy to move through a broker later.

21. **Why JSONL?**  
    It is inspectable, append-friendly, streamable, and simple to replay.

22. **How are event IDs generated?**  
    Each emitted event receives a UUID v4.

23. **How is event ordering guaranteed?**  
    `pipeline.run_all` globally sorts JSONL after all camera clips are processed.

24. **How is POS conversion matched?**  
    A transaction converts an unmatched billing visitor seen in the preceding five-minute window.

25. **How is abandonment generated?**  
    If billing exit has no matching POS transaction, the correlator appends `BILLING_QUEUE_ABANDON`.

26. **Is POS correlation idempotent?**  
    Yes. Existing abandonment keys are skipped on rerun.

27. **Why no customer ID in POS matching?**  
    The challenge explicitly requires store plus time-window correlation.

## Metrics and Anomalies

28. **What is the north-star metric?**  
    Converted visitor sessions divided by unique entrance visitor sessions.

29. **How are re-entries counted in conversion?**  
    They reuse the same visitor token and count once.

30. **How is queue depth calculated?**  
    Count tracked bottom-centre points inside the billing polygon only.

31. **Why latest queue depth, not maximum?**  
    Operations need the current condition; historical peaks belong in time-series analysis.

32. **How does queue-spike detection work?**  
    Current depth must exceed rolling mean plus two standard deviations after three baseline samples.

33. **Why retain a cold-start threshold?**  
    A new store still needs alerts before enough baseline samples exist.

34. **How is conversion drop detected?**  
    Today's rate below 70% of the previous seven-day average emits a warning.

35. **How is dead zone detected?**  
    A historically known non-billing zone with no visit in 30 minutes is flagged.

36. **How is heatmap intensity normalized?**  
    Zone visit frequency is divided by the busiest zone and scaled to 100.

37. **Why flag heatmap confidence below 20 sessions?**  
    Small samples can mislead merchandising decisions.

## API and Storage

38. **How is ingest idempotent?**  
    SQLite uses `event_id` as primary key and `INSERT OR IGNORE`.

39. **How are malformed batches handled?**  
    Records validate independently; valid siblings persist and indexed errors return for bad items.

40. **What happens with invalid JSON?**  
    The API returns `400`, not a `503`.

41. **What happens if SQLite fails?**  
    The global handler returns structured `503`; server logs retain the stack trace.

42. **Why SQLite?**  
    It minimizes acceptance-gate dependencies while providing persistence, indexes, and WAL mode.

43. **What breaks first at 40 stores?**  
    Serialized writes and repeated analytics scans. Add a durable broker and production database.

44. **Why calculate analytics on request?**  
    It keeps challenge behavior simple and fresh. Incremental aggregates are the scale-up path.

45. **Why FastAPI?**  
    Strong Pydantic validation, clear OpenAPI docs, and good scoring-harness compatibility.

## Operations, Docker, and AI

46. **What does `/health` report?**  
    Per-store last event time, lag seconds, and `STALE_FEED` beyond ten minutes.

47. **What is in structured logs?**  
    Trace ID, store, endpoint, latency, event count for ingest, and status.

48. **Why keep CV dependencies outside the API image?**  
    It reduces image size and models the real edge-processing boundary.

49. **Where did AI advice change the design?**  
    It supported the edge/API split; I rejected hosted VLM dependence and tracker-ID-as-session assumptions.

50. **What would you do with one more day?**  
    Obtain official layouts and POS data, label doorway counts, benchmark stride and model size, and calibrate staff/Re-ID thresholds.

