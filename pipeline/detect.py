from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

import cv2
from ultralytics import YOLO

from pipeline.emit import EventEmitter
from pipeline.tracker import BehaviourTracker


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def process_video(video: Path, output: Path, config: dict, *, model_name: str, stride: int, limit_frames: int | None = None) -> int:
    camera = config["cameras"][video.stem]
    started = datetime.fromisoformat(camera["clip_started_at"].replace("Z", "+00:00"))
    emitter = EventEmitter(output, config["store_id"], camera["camera_id"])
    tracker = BehaviourTracker(camera["camera_id"], camera["kind"], camera.get("zones", {}), camera.get("threshold_y"))
    model = YOLO(model_name)
    capture = cv2.VideoCapture(str(video))
    fps = capture.get(cv2.CAP_PROP_FPS) or 25
    frame_index = emitted = 0
    while capture.isOpened():
        ok, frame = capture.read()
        if not ok or (limit_frames is not None and frame_index >= limit_frames):
            break
        if frame_index % stride:
            frame_index += 1
            continue
        timestamp = started + timedelta(seconds=frame_index / fps)
        result = model.track(frame, persist=True, classes=[0], conf=0.18, iou=0.5, verbose=False)[0]
        boxes = result.boxes
        current = []
        if boxes is not None and boxes.id is not None:
            for xyxy, track_id, confidence in zip(boxes.xyxy.cpu().tolist(), boxes.id.int().cpu().tolist(), boxes.conf.cpu().tolist()):
                x1, y1, x2, y2 = xyxy
                current.append((track_id, (int((x1 + x2) / 2), int(y2)), float(confidence)))
        billing_zone = camera.get("zones", {}).get("BILLING")
        queue_depth = sum(
            1
            for _, (x, y), _ in current
            if billing_zone and billing_zone[0] <= x <= billing_zone[2] and billing_zone[1] <= y <= billing_zone[3]
        )
        for track_id, point, confidence in current:
            before = sum(emitter.sequence.values())
            tracker.update(track_id, point, confidence, timestamp, emitter.emit, queue_depth)
            emitted += sum(emitter.sequence.values()) - before
        before = sum(emitter.sequence.values())
        tracker.prune(timestamp, emitter.emit)
        emitted += sum(emitter.sequence.values()) - before
        frame_index += 1
    capture.release()
    return emitted


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect people and emit store behavioural events.")
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("config/store_layout.json"))
    parser.add_argument("--output", type=Path, default=Path("data/events.jsonl"))
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--stride", type=int, default=5, help="Process every Nth frame.")
    parser.add_argument("--limit-frames", type=int)
    args = parser.parse_args()
    config = load_config(args.config)
    emitted = process_video(args.video, args.output, config, model_name=args.model, stride=args.stride, limit_frames=args.limit_frames)
    print(json.dumps({"video": str(args.video), "output": str(args.output), "emitted": emitted}))


if __name__ == "__main__":
    main()
