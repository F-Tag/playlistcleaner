import pandas as pd
import pytest

from playlistcleaner.models import Track
from playlistcleaner.processing import (
    add_title_groups,
    build_dataframe,
    deduplicate,
    mark_alternate_versions,
    mark_duplicate_titles,
    mark_duplicate_trans_titles,
    mark_initial_flags,
    mark_instrumentals,
    mark_live_versions,
    mark_remaining_live_versions,
    mark_remastered,
    normalize_tracks,
)


def _track(
    path: str,
    title: str,
    *,
    artist: str = "Artist",
    album: str = "Album",
    date: str = "2020",
) -> Track:
    return Track(
        path=path,
        tags={
            "TITLE": title,
            "ARTIST": artist,
            "ALBUM": album,
            "DATE": date,
        },
    )


def test_build_dataframe_adds_required_columns_and_drops_untagged_rows() -> None:
    tracks = [
        _track("tagged.mp3", "Song"),
        Track(path="partial.mp3", tags={"TITLE": "No Album", "ARTIST": "Artist"}),
        Track(path="untagged.mp3", tags={"TITLE": "No Tags"}),
    ]

    df = build_dataframe(tracks)

    assert df["path"].tolist() == ["tagged.mp3", "partial.mp3"]
    assert df["ALBUM"].isna().tolist() == [False, True]
    assert df["DATE"].isna().tolist() == [False, True]


def test_build_dataframe_handles_an_empty_playlist() -> None:
    df = build_dataframe([])

    assert df.empty
    assert df.columns.tolist() == ["TITLE", "ARTIST", "ALBUM", "DATE"]


def test_normalize_tracks_normalizes_tags_and_adds_comparison_columns() -> None:
    df = pd.DataFrame(
        {
            "TITLE": ["Song (Live)", None],
            "ARTIST": ["Ａｒｔｉｓｔ", "Artist"],
            "ALBUM": ["Live Album", None],
            "DATE": [None, "2021"],
        }
    )

    result = normalize_tracks(df)

    assert result["TITLE"].tolist() == ["song (live)", ""]
    assert result["ARTIST"].tolist() == ["artist", "artist"]
    assert result["ALBUM"].tolist() == ["live album", ""]
    assert result["DATE"].tolist() == ["0000-00-00", "2021"]
    assert result["is_live"].tolist() == [1, 0]
    assert result["trans_title"].tolist() == ["song", ""]


def test_add_title_groups_groups_prefixed_titles() -> None:
    df = pd.DataFrame(
        {
            "trans_title": ["song", "songlive", "other"],
            "DATE": ["2021", "2020", "2020"],
        }
    )

    result = add_title_groups(df)

    assert result["trans_title"].tolist() == ["other", "song", "songlive"]
    assert result["group_pattern"].tolist() == ["songlive", "other", "song"]
    assert result["title_group"].tolist() == [1, 2, 2]


def test_mark_initial_flags_flags_drama_cds() -> None:
    df = pd.DataFrame({"ARTIST": ["ドラマCD", "artist"]})

    result = mark_initial_flags(df)

    assert result["flag"].tolist() == [True, False]


def test_mark_duplicate_titles_keeps_first_by_live_and_date_priority() -> None:
    df = pd.DataFrame(
        {
            "TITLE": ["song", "song", "other"],
            "ARTIST": ["artist", "artist", "artist"],
            "is_live": [0, 1, 0],
            "DATE": ["2020", "2021", "2020"],
            "flag": [False, False, False],
        }
    )

    result = mark_duplicate_titles(df)

    flagged = result[result["flag"]]
    assert flagged["TITLE"].tolist() == ["song"]
    assert flagged["DATE"].tolist() == ["2021"]


def test_mark_instrumentals_flags_only_matching_titles() -> None:
    df = pd.DataFrame(
        {
            "TITLE": [
                "song",
                "song instrumental",
                "tune instrumental",
                "tune off vocal",
                "solo",
            ],
            "title_group": [1, 1, 2, 2, 3],
            "flag": [False, False, False, False, False],
        }
    )

    result = mark_instrumentals(df)

    assert result["flag"].tolist() == [False, True, False, False, False]


def test_mark_live_versions_keeps_one_when_every_title_matches() -> None:
    df = pd.DataFrame(
        {
            "TITLE": ["song", "song live", "tune live", "tune live 2", "single"],
            "title_group": [1, 1, 2, 2, 3],
            "ARTIST": ["artist"] * 5,
            "flag": [False] * 5,
        }
    )

    result = mark_live_versions(df)

    assert result["flag"].tolist() == [False, True, False, True, False]


def test_mark_alternate_versions_flags_matching_titles() -> None:
    df = pd.DataFrame(
        {
            "TITLE": ["song", "song tv size", "tune remix", "tune remix 2", "solo"],
            "title_group": [1, 1, 2, 2, 3],
            "ARTIST": ["artist"] * 5,
            "flag": [False] * 5,
        }
    )

    result = mark_alternate_versions(df)

    assert result["flag"].tolist() == [False, True, False, True, False]


def test_mark_remastered_adds_remaster_column() -> None:
    df = pd.DataFrame({"TITLE": ["song", "song remastered", "other"]})

    result = mark_remastered(df)

    assert result["is_remaster"].tolist() == [0, 1, 0]


def test_mark_duplicate_trans_titles_flags_duplicates_by_priority() -> None:
    df = pd.DataFrame(
        {
            "TITLE": ["Song (Live)", "Song", "Other"],
            "ARTIST": ["Artist", "Artist", "Artist"],
            "trans_title": ["song", "song", "other"],
            "flag": [False, False, False],
            "is_remaster": [0, 0, 0],
            "is_live": [1, 0, 0],
            "DATE": ["2021", "2020", "2020"],
        }
    )

    result = mark_duplicate_trans_titles(df)

    flags = dict(zip(result["TITLE"], result["flag"], strict=True))
    assert flags == {"Song": False, "Song (Live)": True, "Other": False}


def test_mark_remaining_live_versions_flags_remaining_live_tracks() -> None:
    df = pd.DataFrame(
        {
            "TITLE": ["song", "song live", "tune", "tune live", "solo"],
            "title_group": [1, 1, 2, 2, 3],
            "ARTIST": ["artist"] * 5,
            "is_live": [0, 1, 1, 1, 0],
            "flag": [False] * 5,
        }
    )

    result = mark_remaining_live_versions(df)

    assert result["flag"].tolist() == [False, True, False, True, False]


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("track1.mp3", False),
        ("track2.mp3", True),
        ("track3.mp3", True),
        ("track4.mp3", False),
    ],
)
def test_deduplicate_matches_the_expected_playlist_cleaning(
    path: str, expected: bool
) -> None:
    tracks = [
        _track("track1.mp3", "Song"),
        _track("track2.mp3", "Song"),
        _track("track3.mp3", "Song (Live)", album="Live Album", date="2021"),
        _track("track4.mp3", "Other"),
    ]

    result = deduplicate(tracks)

    flags = dict(zip(result["path"], result["flag"], strict=True))
    assert bool(flags[path]) is expected
    assert result["flag"].sum() == 2
    assert set(result.loc[~result["flag"], "path"]) == {"track1.mp3", "track4.mp3"}
