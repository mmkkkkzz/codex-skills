---
name: video-meeting-minutes
description: Generate, inspect, and refine meeting minutes from local video files using the /Users/mk/Developer/video-meeting-minutes CLI. Use when the user asks to transcribe an mp4, run ElevenLabs Scribe v2 diarization, analyze screen-change frames, regenerate frame_analysis.json, or regenerate minutes.md from existing outputs.
---

# Video Meeting Minutes

## Overview

Use the local `video-meeting-minutes` repo as the implementation. This skill is an operation guide and thin helper layer for repeatable meeting-video workflows.

Default repo:

```bash
/Users/mk/Developer/video-meeting-minutes
```

## Safety Rules

- Do not print `.env` contents or API keys.
- Do not commit `.env`, input videos, `.DS_Store`, or generated `output/` artifacts unless the user explicitly asks.
- Before overwriting `vision/frame_analysis.json` or `minutes.md`, create a timestamped backup in the same directory.
- Prefer `uv` from the target repo.
- ElevenLabs is the only direct external transcription API. Frame analysis and minutes generation go through Codex app-server.

## Defaults

- Transcription: ElevenLabs Scribe v2, `ELEVENLABS_SCRIBE_MODEL=scribe_v2`.
- Diarization: enabled by default. Use `--no-diarize` only when the user asks.
- Frame analysis: Codex app-server, `CODEX_VISION_MODEL=gpt-5.5`, `CODEX_VISION_EFFORT=high`.
- Minutes generation: Codex app-server, `CODEX_MINUTES_MODEL=gpt-5.5`, `CODEX_MINUTES_EFFORT=xhigh`.
- Minutes template:
  - `参加者`
  - `決定事項`
  - `TODO`
  - `発言要旨`
- `TODO` must be a Markdown table with 5W1H-level detail.
- `発言要旨` must be topic-based, not chronological, with no timestamps. Each topic uses `論点`, `参加者の意見`, `結果`.

## Full Run

From `/Users/mk/Developer/video-meeting-minutes`:

```bash
uv run video-meeting-minutes path/to/meeting.mp4
```

Useful variants:

```bash
uv run video-meeting-minutes path/to/meeting.mp4 --keyterms 勤怠管理 受給者証 事業所 ヘルパー 監査ログ ログインID
uv run video-meeting-minutes path/to/meeting.mp4 --no-diarize
uv run video-meeting-minutes path/to/meeting.mp4 --skip-vision --skip-minutes
```

After a run, report the paths for:

- `minutes.md`
- `transcript/elevenlabs_scribe_v2.txt`
- `vision/frame_analysis.json`
- `manifest.json`

## Reanalyze Frames Only

Use this when the frame-analysis prompt changed or the user asks to rerun only visual analysis. Do not retranscribe audio and do not regenerate minutes unless requested.

```bash
cd /Users/mk/Developer/video-meeting-minutes
uv run python /Users/mk/Developer/codex-skills/skills/video-meeting-minutes/scripts/reanalyze_frames.py \
  --run-dir output/<run-dir>
```

The helper reads `vision/frames.json`, backs up the existing `vision/frame_analysis.json`, and writes the regenerated detailed analysis to the same path.

## Regenerate Minutes Only

Use this after changing the minutes prompt, TODO structure, or frame analysis. Do not retranscribe audio or reanalyze frames.

```bash
cd /Users/mk/Developer/video-meeting-minutes
uv run python /Users/mk/Developer/codex-skills/skills/video-meeting-minutes/scripts/regenerate_minutes.py \
  --run-dir output/<run-dir>
```

The helper reads:

- `transcript/elevenlabs_scribe_v2.json`
- `vision/frame_analysis.json`

It backs up `minutes.md` and writes the regenerated minutes to the same path.

## Output Review

When checking the generated minutes, inspect:

- Headings: exactly the main sections expected by the template.
- TODO: Markdown table with clear topic, owner, target screen/function, action, reason, deadline.
- `発言要旨`: topic-level `###` sections, no timestamps, each with `論点`, `参加者の意見`, `結果`.
- Low-value chatter such as greetings, thanks, screen-sharing setup, and simple acknowledgements should not appear.

## Common Follow-ups

- If frame analysis is too shallow, update the frame prompt in `video_meeting_minutes/codex_tools.py`, then run "Reanalyze Frames Only".
- If minutes structure is wrong, update the minutes prompt in `video_meeting_minutes/codex_tools.py`, then run "Regenerate Minutes Only".
- If speaker separation is needed, ensure the full run uses default diarization or explicitly pass `--diarize`.
