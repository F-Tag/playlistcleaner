# playlistcleaner

M3U8 プレイリストから重複している曲を検出し、整理するスクリプトです。

## セットアップ

[uv](https://docs.astral.sh/uv/) を使って依存関係をインストールします。

```sh
uv sync
```

音楽ファイルのタグ読み取りに [TagLib](https://taglib.org/) を使うため、
`pytaglib` が利用するネイティブライブラリが必要です。

## 使い方

```sh
uv run python cleaner.py path/to/playlist.m3u8
```

- `output/<プレイリスト名>.tsv` に判定結果を出力します。
- 元のプレイリストは `OLD_<プレイリスト名>` にリネームされます。
- 重複と判定されなかった曲だけを含む新しいプレイリストを生成します。

## 開発

```sh
uv run ruff check .
uv run ruff format .
uv run bandit -c pyproject.toml -r cleaner.py
```
