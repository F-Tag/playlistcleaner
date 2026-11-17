from pathlib import Path
from types import SimpleNamespace

import pytest

from playlistcleaner import metadata
from playlistcleaner.models import Track


class FakeSong:
    def __init__(self, tags: dict[str, list[str]]) -> None:
        self.tags = tags

    def __enter__(self) -> "FakeSong":
        return self

    def __exit__(self, *args: object) -> None:
        return None


@pytest.mark.parametrize("absolute", [False, True])
def test_read_track_reads_first_value_and_relative_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, absolute: bool
) -> None:
    playlist = tmp_path / "playlist.m3u8"
    playlist.write_text("", encoding="utf-8")
    audio = tmp_path / "song.mp3"
    audio.write_bytes(b"dummy")
    seen: dict[str, object] = {}

    def fake_file(path: Path, save_on_exit: bool) -> FakeSong:
        seen["path"] = path
        seen["save_on_exit"] = save_on_exit
        return FakeSong({"TITLE": ["Song"], "ARTIST": ["Artist", "Other"], "EMPTY": []})

    monkeypatch.setattr(metadata, "taglib", SimpleNamespace(File=fake_file))
    source = audio if absolute else "song.mp3"

    track = metadata.read_track(source, playlist)

    assert track.path == "song.mp3"
    assert track.tags == {"TITLE": "Song", "ARTIST": "Artist"}
    assert seen["save_on_exit"] is False
    assert isinstance(seen["path"], Path)
    assert seen["path"] == audio.resolve()


def test_read_tracks_reads_each_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[tuple[str, Path]] = []

    def fake_read_track(path: str, playlist_path: Path) -> Track:
        calls.append((path, playlist_path))
        return Track(path=path, tags={})

    monkeypatch.setattr(metadata, "read_track", fake_read_track)
    playlist = tmp_path / "playlist.m3u8"

    tracks = metadata.read_tracks(["one.mp3", "two.mp3"], playlist, show_progress=False)

    assert [track.path for track in tracks] == ["one.mp3", "two.mp3"]
    assert calls == [("one.mp3", playlist), ("two.mp3", playlist)]


def test_read_tracks_enables_progress_by_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    seen: dict[str, object] = {}

    def fake_tqdm(iterable: list[str], *, desc: str, disable: bool) -> list[str]:
        seen["desc"] = desc
        seen["disable"] = disable
        return iterable

    monkeypatch.setattr(metadata, "tqdm", fake_tqdm)
    monkeypatch.setattr(metadata, "read_track", lambda path, _: Track(path, {}))

    metadata.read_tracks(["one.mp3"], tmp_path / "playlist.m3u8")

    assert seen == {"desc": "read music metadata", "disable": False}
