# playlistcleaner

M3U8 プレイリストから重複している曲を検出し、整理する CLI ツールです。

## 必要要件

- Python 3.11 以上
- [uv](https://docs.astral.sh/uv/)
- [TagLib](https://taglib.org/)（`pytaglib` が利用するネイティブライブラリ）

## セットアップ

```sh
uv sync
```

## 使い方

```sh
uv run playlistcleaner path/to/playlist.m3u8
```

または、モジュールとして実行できます。

```sh
uv run python -m playlistcleaner path/to/playlist.m3u8
```

- `output/<プレイリスト名>.tsv` に判定結果を出力します。
- 元のプレイリストは `OLD_<プレイリスト名>` にリネームされます。
- 重複と判定されなかった曲だけを含む新しいプレイリストを生成します。

## プロジェクト構成

```text
.
├── .github/                  # CI / CodeQL / Dependabot
├── archive/                  # メンテナンス対象外の旧スクリプト
├── src/
│   └── playlistcleaner/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py            # CLI エントリポイント
│       ├── metadata.py       # 音声ファイルのタグ読み取り
│       ├── models.py         # データモデル
│       ├── normalization.py  # 表記ゆれの正規化
│       ├── playlist.py       # M3U8 入出力・レポート出力
│       └── processing.py     # 重複判定パイプライン
├── tests/
├── pyproject.toml
├── uv.lock
└── README.md
```

## 開発

```sh
uv run ruff check .
uv run ruff format .
uv run bandit -c pyproject.toml -r src
uv run pytest --cov --cov-report=term-missing
```

テストはカバレッジ付きで実行でき、90% を下回ると失敗します。
CI の Test ジョブではカバレッジレポートを Job Summary にも表示します。

`duplicates.vbs` は foobar2000 用の旧スクリプトとして `archive/` に保管しています。
