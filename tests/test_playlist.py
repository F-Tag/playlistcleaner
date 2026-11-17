from pathlib import Path

import pandas as pd
import pytest

from playlistcleaner.playlist import (
    archive_playlist,
    read_playlist,
    report_columns,
    save_results,
    write_playlist,
    write_report,
)


def _dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "path": ["drop.mp3", "keep.mp3"],
            "TITLE": ["Drop", "Keep"],
            "ARTIST": ["Artist", "Artist"],
            "ALBUM": ["Album", "Album"],
            "flag": [True, False],
            "trans_title": ["drop", "keep"],
            "title_group": [2, 1],
            "DATE": ["2020", "2020"],
        }
    )


def test_read_playlist_skips_comments_blank_lines_and_bom(tmp_path: Path) -> None:
    playlist = tmp_path / "list.m3u8"
    playlist.write_text(
        "\ufeff#EXTM3U\nfirst.mp3\n\n  # comment\n second.mp3 \n",
        encoding="utf-8",
    )

    assert read_playlist(playlist) == ["first.mp3", "second.mp3"]


def test_report_columns_puts_priority_columns_first() -> None:
    df = pd.DataFrame({"path": [], "TITLE": [], "flag": []})

    assert report_columns(df) == [
        "TITLE",
        "ARTIST",
        "ALBUM",
        "flag",
        "trans_title",
        "title_group",
        "path",
    ]


def test_write_report_creates_sorted_tsv(tmp_path: Path) -> None:
    playlist = tmp_path / "list.m3u8"

    report = write_report(_dataframe(), playlist, output_dir=tmp_path / "out")

    assert report == tmp_path / "out" / "list.tsv"
    written = pd.read_csv(report, sep="\t", index_col=0)
    assert written["path"].tolist() == ["keep.mp3", "drop.mp3"]
    assert written.columns[:6].tolist() == [
        "TITLE",
        "ARTIST",
        "ALBUM",
        "flag",
        "trans_title",
        "title_group",
    ]


def test_archive_playlist_moves_file_to_old_name(tmp_path: Path) -> None:
    playlist = tmp_path / "list.m3u8"
    playlist.write_text("content", encoding="utf-8")

    archived = archive_playlist(playlist)

    assert archived == tmp_path / "OLD_list.m3u8"
    assert not playlist.exists()
    assert archived.read_text(encoding="utf-8") == "content"


def test_write_playlist_writes_unflagged_paths_in_original_order(
    tmp_path: Path,
) -> None:
    playlist = tmp_path / "list.m3u8"
    df = pd.DataFrame(
        {"path": ["first.mp3", "drop.mp3", "last.mp3"], "flag": [False, True, False]},
        index=[2, 0, 1],
    )

    write_playlist(df, playlist)

    assert playlist.read_text(encoding="utf-8").splitlines() == [
        "last.mp3",
        "first.mp3",
    ]


def test_save_results_writes_report_archives_and_replaces_playlist(
    tmp_path: Path,
) -> None:
    playlist = tmp_path / "list.m3u8"
    playlist.write_text("drop.mp3\nkeep.mp3\n", encoding="utf-8")

    report = save_results(_dataframe(), playlist, output_dir=tmp_path / "out")

    assert report.exists()
    assert playlist.read_text(encoding="utf-8").splitlines() == ["keep.mp3"]
    assert (tmp_path / "OLD_list.m3u8").read_text(encoding="utf-8") == (
        "drop.mp3\nkeep.mp3\n"
    )


def test_save_results_uses_default_output_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    playlist = tmp_path / "list.m3u8"
    playlist.write_text("drop.mp3\nkeep.mp3\n", encoding="utf-8")

    report = save_results(_dataframe(), playlist)

    assert report == Path("output") / "list.tsv"
    assert report.exists()
