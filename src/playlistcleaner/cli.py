import argparse
from collections.abc import Sequence
from pathlib import Path

from playlistcleaner.metadata import read_tracks
from playlistcleaner.playlist import DEFAULT_OUTPUT_DIR, read_playlist, save_results
from playlistcleaner.processing import deduplicate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="playlistcleaner",
        description="M3U8 プレイリストから重複している曲を整理します。",
    )
    parser.add_argument("playlist", type=Path, help="整理する M3U8 プレイリスト")
    return parser


def run(playlist: Path, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    """プレイリストを読み込み、重複を除外して保存する。"""
    entries = read_playlist(playlist)
    tracks = read_tracks(entries, playlist)
    df = deduplicate(tracks)
    return save_results(df, playlist, output_dir=output_dir)


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    run(args.playlist)
