import importlib
import runpy
import sys
from pathlib import Path

import pandas as pd
import pytest

from playlistcleaner import cli
from playlistcleaner.models import Track


def test_build_parser_accepts_a_playlist() -> None:
    args = cli.build_parser().parse_args(["path/to/playlist.m3u8"])

    assert args.playlist == Path("path/to/playlist.m3u8")


def test_run_reads_and_processes_the_playlist(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    playlist = tmp_path / "list.m3u8"
    output_dir = tmp_path / "out"
    tracks = [Track(path="song.mp3", tags={"TITLE": "Song"})]
    df = pd.DataFrame({"path": ["song.mp3"], "flag": [False]})
    report = output_dir / "list.tsv"
    calls: dict[str, object] = {}

    def fake_read_playlist(path: Path) -> list[str]:
        calls["playlist"] = path
        return ["song.mp3"]

    def fake_read_tracks(entries: list[str], path: Path) -> list[Track]:
        calls["entries"] = entries
        calls["read_tracks_playlist"] = path
        return tracks

    def fake_deduplicate(value: list[Track]) -> pd.DataFrame:
        calls["tracks"] = value
        return df

    def fake_save_results(value: pd.DataFrame, path: Path, output_dir: Path) -> Path:
        calls["saved"] = (value, path, output_dir)
        return report

    monkeypatch.setattr(cli, "read_playlist", fake_read_playlist)
    monkeypatch.setattr(cli, "read_tracks", fake_read_tracks)
    monkeypatch.setattr(cli, "deduplicate", fake_deduplicate)
    monkeypatch.setattr(cli, "save_results", fake_save_results)

    result = cli.run(playlist, output_dir=output_dir)

    assert result == report
    assert calls == {
        "playlist": playlist,
        "entries": ["song.mp3"],
        "read_tracks_playlist": playlist,
        "tracks": tracks,
        "saved": (df, playlist, output_dir),
    }


def test_main_runs_the_playlist(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    playlist = tmp_path / "list.m3u8"
    seen: list[Path] = []

    monkeypatch.setattr(cli, "run", lambda path: seen.append(path))

    cli.main([str(playlist)])

    assert seen == [playlist]


def test_main_requires_a_playlist_argument() -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main([])

    assert excinfo.value.code == 2


def test_module_entry_point_calls_main(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []

    monkeypatch.setattr(cli, "main", lambda: calls.append(True))
    monkeypatch.setattr(sys, "argv", ["playlistcleaner"])

    runpy.run_module("playlistcleaner", run_name="__main__")

    assert calls == [True]


def test_main_module_does_nothing_when_imported() -> None:
    module = importlib.import_module("playlistcleaner.__main__")

    assert module is not None
