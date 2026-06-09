---
name: video-meeting-minutes
description: /Users/mk/Developer/video-meeting-minutes CLIを使って、ローカル動画から議事録を生成・確認・再生成する。mp4の文字起こし、ElevenLabs Scribe v2の話者分離、画面変化フレーム解析、frame_analysis.jsonの再生成、既存出力からminutes.mdを再生成する依頼で使う。
---

# Video Meeting Minutes

## 概要

実装本体はローカルの `video-meeting-minutes` repoを使う。このskillは、会議動画から議事録を作る運用手順と、再実行用の薄い補助scriptをまとめたもの。

デフォルトrepo:

```bash
/Users/mk/Developer/video-meeting-minutes
```

## 安全ルール

- `.env`の中身やAPIキーは表示しない。
- ユーザーが明示しない限り、`.env`、入力動画、`.DS_Store`、生成済みの`output/`成果物はcommitしない。
- `vision/frame_analysis.json`や`minutes.md`を上書きする前に、同じディレクトリへタイムスタンプ付きbackupを作る。
- 対象repoでは`uv`を使う。
- 直接使う外部文字起こしAPIはElevenLabsだけ。フレーム解析と議事録生成はCodex app-server経由で行う。

## デフォルト設定

- 文字起こし: ElevenLabs Scribe v2、`ELEVENLABS_SCRIBE_MODEL=scribe_v2`
- 話者分離: デフォルトON。ユーザーが求めた場合だけ`--no-diarize`で無効化する。
- フレーム解析: Codex app-server、`CODEX_VISION_MODEL=gpt-5.5`、`CODEX_VISION_EFFORT=high`
- 議事録生成: Codex app-server、`CODEX_MINUTES_MODEL=gpt-5.5`、`CODEX_MINUTES_EFFORT=xhigh`
- 議事録テンプレート:
  - `参加者`
  - `決定事項`
  - `TODO`
  - `発言要旨`
- `TODO`はMarkdown表にし、5W1Hが分かる粒度で書く。
- `発言要旨`は時系列ではなくトピック別にする。時間は書かない。各トピックは`論点`、`参加者の意見`、`結果`で整理する。

## フル実行

`/Users/mk/Developer/video-meeting-minutes`で実行する。

```bash
uv run video-meeting-minutes path/to/meeting.mp4
```

よく使う派生:

```bash
uv run video-meeting-minutes path/to/meeting.mp4 --keyterms 勤怠管理 受給者証 事業所 ヘルパー 監査ログ ログインID
uv run video-meeting-minutes path/to/meeting.mp4 --no-diarize
uv run video-meeting-minutes path/to/meeting.mp4 --skip-vision --skip-minutes
```

実行後は、少なくとも次のパスを報告する。

- `minutes.md`
- `transcript/elevenlabs_scribe_v2.txt`
- `vision/frame_analysis.json`
- `manifest.json`

## フレーム解析だけ再実行

フレーム解析プロンプトを変更した時、またはユーザーが画像解析だけの再実行を求めた時に使う。音声文字起こしは再実行しない。ユーザーが求めない限り議事録も再生成しない。

```bash
cd /Users/mk/Developer/video-meeting-minutes
uv run python /Users/mk/Developer/codex-skills/skills/video-meeting-minutes/scripts/reanalyze_frames.py \
  --run-dir output/<run-dir>
```

この補助scriptは`vision/frames.json`を読み、既存の`vision/frame_analysis.json`をbackupしてから、同じパスへ詳細なフレーム解析を再生成する。

## 議事録だけ再生成

議事録プロンプト、TODO構造、フレーム解析を変更した後に使う。音声文字起こしやフレーム解析は再実行しない。

```bash
cd /Users/mk/Developer/video-meeting-minutes
uv run python /Users/mk/Developer/codex-skills/skills/video-meeting-minutes/scripts/regenerate_minutes.py \
  --run-dir output/<run-dir>
```

この補助scriptは次を読む。

- `transcript/elevenlabs_scribe_v2.json`
- `vision/frame_analysis.json`

既存の`minutes.md`をbackupしてから、同じパスへ議事録を再生成する。

## 出力確認

生成された議事録では次を確認する。

- 見出し: テンプレートの主要セクションになっていること。
- TODO: Markdown表で、トピック、担当者、対象画面/機能、作業内容、理由・背景、期限が明確なこと。
- `発言要旨`: トピックごとの`###`小見出しがあり、時間表記がなく、各トピックが`論点`、`参加者の意見`、`結果`で整理されていること。
- 挨拶、謝意、画面共有の段取り、単なる相づちのような参照価値の低い会話が入っていないこと。

## よくある追加対応

- フレーム解析が浅い場合は、`video_meeting_minutes/codex_tools.py`のフレーム解析プロンプトを修正してから「フレーム解析だけ再実行」を行う。
- 議事録の構造が悪い場合は、`video_meeting_minutes/codex_tools.py`の議事録プロンプトを修正してから「議事録だけ再生成」を行う。
- 話者分離が必要な場合は、フル実行でデフォルトのdiarize ONを使う。明示するなら`--diarize`を付ける。
