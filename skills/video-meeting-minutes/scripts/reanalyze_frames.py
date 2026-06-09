from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


DEFAULT_REPO = Path("/Users/mk/Developer/video-meeting-minutes")


def normalize_model(value: str | None) -> str | None:
    if value == "gpt5.5":
        return "gpt-5.5"
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Re-run Codex frame analysis for an existing video-meeting-minutes output.")
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=1200)
    parser.add_argument("--keep-stderr", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = args.repo.expanduser().resolve()
    run_dir = args.run_dir
    if not run_dir.is_absolute():
        run_dir = repo / run_dir
    run_dir = run_dir.resolve()

    sys.path.insert(0, str(repo))
    from video_meeting_minutes.codex_app import CodexAppServerClient
    from video_meeting_minutes.codex_tools import analyze_frames
    from video_meeting_minutes.models import FrameEvent

    load_dotenv(dotenv_path=repo / ".env")

    frames_json = run_dir / "vision" / "frames.json"
    analysis_json = run_dir / "vision" / "frame_analysis.json"
    if not frames_json.exists():
        raise FileNotFoundError(frames_json)

    if analysis_json.exists():
        backup = analysis_json.with_name(f"frame_analysis.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        shutil.copy2(analysis_json, backup)
        print(f"Backed up previous analysis: {backup}", flush=True)

    raw_frames = json.loads(frames_json.read_text(encoding="utf-8"))
    frames: list[FrameEvent] = []
    for item in raw_frames:
        image_path = Path(item["path"])
        if not image_path.is_absolute():
            image_path = repo / image_path
        frames.append(
            FrameEvent(
                index=int(item["index"]),
                timestamp=float(item["timestamp"]),
                path=image_path,
                diff_score=float(item.get("diff_score") or 0),
            )
        )

    base_model = normalize_model(os.getenv("CODEX_MODEL") or "gpt-5.5")
    vision_model = normalize_model(os.getenv("CODEX_VISION_MODEL") or base_model)
    vision_effort = os.getenv("CODEX_VISION_EFFORT") or os.getenv("CODEX_EFFORT") or "medium"

    print(f"Reanalyzing {len(frames)} frames with model={vision_model}, effort={vision_effort}", flush=True)
    with CodexAppServerClient(
        cwd=repo,
        model=base_model,
        timeout_seconds=args.timeout,
        keep_stderr=args.keep_stderr,
    ) as client:
        analyze_frames(frames, client=client, output_path=analysis_json, model=vision_model, effort=vision_effort)

    print(f"Saved detailed frame analysis: {analysis_json}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
