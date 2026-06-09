---
name: video-meeting-minutes
description: グローバルインストール済みの`video-meeting-minutes` CLI（ラッパー`vmm`）で、ローカル動画から議事録を生成・確認・再生成する。mp4の文字起こし、ElevenLabs Scribe v2の話者分離、画面変化フレーム解析、frame_analysis.jsonの再生成、既存出力からminutes.mdを再生成する依頼で使う。
---

# Video Meeting Minutes

## 概要

`video-meeting-minutes`は`uv tool install --editable`で**グローバルインストール済み**のCLIで、どのディレクトリからでも実行できる（`uv run`や`cd`は不要）。このskillは、会議動画から議事録を作る運用手順と、再実行用の薄い補助scriptをまとめたもの。

実装本体（ソースと再実行用script）は次のrepoにある。エディタブルインストールなので、ここのコードを編集すればグローバルコマンドにも即反映される。

```bash
/Users/mk/Developer/video-meeting-minutes
```

実行ファイルの場所:

```bash
~/.local/bin/video-meeting-minutes
```

`~/.zshrc`にラッパー関数`vmm`が定義済みで、repoの`.env`を読み込んでからグローバルCLIを起動する。インタラクティブシェルでは`vmm`を使うのが基本。

```bash
# ~/.zshrc に定義済み
vmm() {
  set -a && source /Users/mk/Developer/video-meeting-minutes/.env && set +a
  video-meeting-minutes "$@"
}
```

## 安全ルール

- `.env`の中身やAPIキーは表示しない。env読み込みは`source`で行い、`cat`等で中身を出さない。
- ユーザーが明示しない限り、`.env`、入力動画、`.DS_Store`、生成済みの`output/`成果物はcommitしない。
- `vision/frame_analysis.json`や`minutes.md`を上書きする前に、同じディレクトリへタイムスタンプ付きbackupを作る。
- 補助script（再実行）は対象repo内で`uv`を使う。
- 直接使う外部文字起こしAPIはElevenLabsだけ。フレーム解析と議事録生成はCodex app-server経由で行う。

## 前提

- グローバル実行には`ELEVENLABS_API_KEY`等のenvが必要。APIキーの実体はrepoの`.env`の1ヶ所だけに置く（`~/.zshrc`等へ複製しない）。
- `vmm`はenv読み込みを自動で行う。`vmm`が使えない環境（非インタラクティブシェル、スクリプト内など）では、素のコマンドの前にrepoの`.env`を読み込む:

  ```bash
  set -a && source /Users/mk/Developer/video-meeting-minutes/.env && set +a
  video-meeting-minutes path/to/meeting.mp4
  ```

- Codex側は`codex login`済みであること。
- `ffmpeg` / `ffprobe`が利用可能であること。

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

どのディレクトリからでも実行できる（env読み込みは`vmm`が自動で行う）。

```bash
vmm path/to/meeting.mp4
```

よく使う派生:

```bash
vmm path/to/meeting.mp4 --keyterms 勤怠管理 受給者証 事業所 ヘルパー 監査ログ ログインID
vmm path/to/meeting.mp4 --no-diarize
vmm path/to/meeting.mp4 --skip-vision --skip-minutes
```

出力先を固定したい場合は`--output-dir`に絶対パスを渡す:

```bash
vmm path/to/meeting.mp4 --output-dir /Users/mk/Developer/video-meeting-minutes/output
```

## 出力場所

`--output-dir`未指定時は、**コマンドを実行したカレントディレクトリ**の`output/`配下に作られる。

```text
<実行したディレクトリ>/output/<動画名>_<YYYYMMDD_HHMMSS>/
  audio/<動画名>.m4a
  frames/frame_*.jpg
  transcript/elevenlabs_scribe_v2.txt
  transcript/elevenlabs_scribe_v2.json
  vision/frames.json
  vision/frame_analysis.json
  manifest.json
  minutes.md
```

実行ごとにタイムスタンプ付きディレクトリが作られるため、上書きされない。実行完了時に`Saved minutes: <フルパス>`が表示される。実行後は、少なくとも次のパスを報告する。

- `minutes.md`
- `transcript/elevenlabs_scribe_v2.txt`
- `vision/frame_analysis.json`
- `manifest.json`

## フレーム解析だけ再実行

フレーム解析プロンプトを変更した時、またはユーザーが画像解析だけの再実行を求めた時に使う。音声文字起こしは再実行しない。ユーザーが求めない限り議事録も再生成しない。

補助scriptはrepoの`.venv`内のパッケージを使うため、repo内で`uv run`する。

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

- フレーム解析が浅い場合は、`video_meeting_minutes/codex_tools.py`のフレーム解析プロンプトを修正してから「フレーム解析だけ再実行」を行う。エディタブルインストールなので再インストール不要で反映される。
- 議事録の構造が悪い場合は、`video_meeting_minutes/codex_tools.py`の議事録プロンプトを修正してから「議事録だけ再生成」を行う。
- 話者分離が必要な場合は、フル実行でデフォルトのdiarize ONを使う。明示するなら`--diarize`を付ける。
- `vmm: command not found`の場合は、`~/.zshrc`の`vmm`関数定義を確認するか、新しいシェルを開く（または前提セクションの素のコマンド＋env読み込みで代替する）。
- `video-meeting-minutes: command not found`の場合は再インストール:
  ```bash
  cd /Users/mk/Developer/video-meeting-minutes
  uv tool install --force --editable . --python 3.11 --python-preference only-managed
  ```
- `pyproject.toml`の依存を変更した時も、上記`--force`で入れ直す（ソース編集だけなら不要）。
