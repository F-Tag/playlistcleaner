from collections.abc import Sequence
from os.path import relpath
from pathlib import Path

import taglib
from tqdm import tqdm

from playlistcleaner.models import Track


def _path_for_playlist(source: Path, playlist_path: Path) -> str:
    """プレイリストに記録するパスを返す。

    相対パスを計算できる場合は相対パス、計算できない場合は絶対パスを返す。
    """
    try:
        return relpath(source, playlist_path.parent)
    except ValueError:
        # Windows ではドライブが異なると relpath が ValueError を送出する。
        # Unix では異なるマウント間でも相対パスを計算できるため、通常はここに来ない。
        return str(source)


def read_track(path: str | Path, playlist_path: Path) -> Track:
    """音声ファイルからタグを読み取り、プレイリストに記録するパスを付与する。"""
    source = Path(path)
    if not source.is_absolute():
        source = (playlist_path.parent / source).resolve(strict=True)

    with taglib.File(source, save_on_exit=False) as song:
        tags = {key: values[0] for key, values in song.tags.items() if values}

    return Track(path=_path_for_playlist(source, playlist_path), tags=tags)


def read_tracks(
    paths: Sequence[str], playlist_path: Path, *, show_progress: bool = True
) -> list[Track]:
    """プレイリスト内の全曲のタグを読み取る。"""
    return [
        read_track(path, playlist_path)
        for path in tqdm(paths, desc="read music metadata", disable=not show_progress)
    ]
