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
    parser = argparse.ArgumentParser(description="Regenerate minutes.md from an existing transcript and frame analysis.")
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--video-name", default=None)
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
    from video_meeting_minutes.codex_tools import generate_minutes
    from video_meeting_minutes.models import FrameAnalysis
    from video_meeting_minutes.scribe import transcript_segments

    load_dotenv(dotenv_path=repo / ".env")

    transcript_json = run_dir / "transcript" / "elevenlabs_scribe_v2.json"
    analysis_json = run_dir / "vision" / "frame_analysis.json"
    minutes_path = run_dir / "minutes.md"
    manifest_path = run_dir / "manifest.json"
    if not transcript_json.exists():
        raise FileNotFoundError(transcript_json)
    if not analysis_json.exists():
        raise FileNotFoundError(analysis_json)

    if minutes_path.exists():
        backup = minutes_path.with_name(f"minutes.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        shutil.copy2(minutes_path, backup)
        print(f"Backed up previous minutes: {backup}", flush=True)

    transcript = json.loads(transcript_json.read_text(encoding="utf-8"))
    segments = transcript_segments(transcript)
    raw_analyses = json.loads(analysis_json.read_text(encoding="utf-8"))
    analyses = [
        FrameAnalysis(
            index=int(item["index"]),
            timestamp=float(item["timestamp"]),
            image_path=Path(item["image_path"]),
            analysis=str(item["analysis"]),
        )
        for item in raw_analyses
    ]

    video_name = args.video_name
    if not video_name and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        video_name = Path(str(manifest.get("video", ""))).name or None
    video_name = video_name or run_dir.name

    base_model = normalize_model(os.getenv("CODEX_MODEL") or "gpt-5.5")
    minutes_model = normalize_model(os.getenv("CODEX_MINUTES_MODEL") or base_model)
    minutes_effort = os.getenv("CODEX_MINUTES_EFFORT") or os.getenv("CODEX_EFFORT") or "medium"

    print(
        f"Regenerating minutes with {len(segments)} transcript segments and {len(analyses)} frame analyses",
        flush=True,
    )
    print(f"model={minutes_model}, effort={minutes_effort}", flush=True)
    with CodexAppServerClient(
        cwd=repo,
        model=base_model,
        timeout_seconds=args.timeout,
        keep_stderr=args.keep_stderr,
    ) as client:
        minutes = generate_minutes(
            client=client,
            video_name=video_name,
            transcript_segments=segments,
            frame_analyses=analyses,
            model=minutes_model,
            effort=minutes_effort,
        )

    minutes_path.write_text(minutes + "\n", encoding="utf-8")
    print(f"Saved regenerated minutes: {minutes_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
