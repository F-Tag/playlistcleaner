from collections.abc import Sequence
from os.path import relpath
from pathlib import Path

import taglib
from tqdm import tqdm

from playlistcleaner.models import Track


def read_track(path: str | Path, playlist_path: Path) -> Track:
    """音声ファイルからタグを読み取り、プレイリストからの相対パスを付与する。"""
    source = Path(path)
    if not source.is_absolute():
        source = (playlist_path.parent / source).resolve(strict=True)

    with taglib.File(source, save_on_exit=False) as song:
        tags = {key: values[0] for key, values in song.tags.items() if values}

    return Track(path=str(relpath(source, playlist_path.parent)), tags=tags)


def read_tracks(
    paths: Sequence[str], playlist_path: Path, *, show_progress: bool = True
) -> list[Track]:
    """プレイリスト内の全曲のタグを読み取る。"""
    return [
        read_track(path, playlist_path)
        for path in tqdm(paths, desc="read music metadata", disable=not show_progress)
    ]
