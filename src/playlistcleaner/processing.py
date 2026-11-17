import re
from collections.abc import Sequence

import pandas as pd
from numpy import roll

from playlistcleaner.models import Track
from playlistcleaner.normalization import (
    ALTERNATE_VERSION_PATTERN,
    INSTRUMENTAL_PATTERN,
    LIVE_ALBUM_PATTERN,
    LIVE_TITLE_PATTERN,
    REMASTER_PATTERN,
    normalize_text,
    simplify_title,
)

REQUIRED_COLUMNS = ("TITLE", "ARTIST", "ALBUM", "DATE")
DEDUP_SORT_COLUMNS = ["trans_title", "flag", "is_remaster", "is_live", "DATE"]
DEDUP_SORT_ASCENDING = [True, True, False, True, False]


def build_dataframe(tracks: Sequence[Track]) -> pd.DataFrame:
    """曲データからタグを列に持つ DataFrame を構築する。"""
    records = [{**track.tags, "path": track.path} for track in tracks]
    df = pd.DataFrame.from_records(records)

    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            df[column] = None

    return df[~df[["ARTIST", "ALBUM"]].isna().all(axis=1)].copy()


def normalize_tracks(df: pd.DataFrame) -> pd.DataFrame:
    """比較用の正規化列とライブ判定列を追加する。"""
    df = df.copy()

    for column in ("ARTIST", "TITLE", "ALBUM"):
        df[column] = df[column].fillna("").map(normalize_text)

    df["DATE"] = df["DATE"].fillna("0000-00-00")
    df["is_live"] = df["ALBUM"].str.contains(LIVE_ALBUM_PATTERN, regex=True).astype(int)
    df["trans_title"] = df["TITLE"].map(simplify_title)
    return df


def add_title_groups(df: pd.DataFrame) -> pd.DataFrame:
    """似たタイトルをまとめるためのグループ番号を付与する。"""
    df = df.sort_values(["trans_title", "DATE"], ascending=[True, False]).copy()
    patterns = roll(df["trans_title"].to_numpy(), 1)
    title_groups: list[int] = []
    group = 0

    for pattern, title in zip(patterns, df["trans_title"], strict=True):
        if not re.match("^" + re.escape(str(pattern)), title):
            group += 1
        title_groups.append(group)

    df["group_pattern"] = patterns
    df["title_group"] = title_groups
    return df


def mark_initial_flags(df: pd.DataFrame) -> pd.DataFrame:
    """ドラマCDを除外対象として初期フラグを設定する。"""
    df = df.copy()
    df["flag"] = False
    df.loc[df["ARTIST"] == "ドラマCD", "flag"] = True
    return df


def mark_duplicate_titles(df: pd.DataFrame) -> pd.DataFrame:
    """タイトルとアーティストが完全一致する重複曲にフラグを立てる。"""
    df = df.sort_values(
        ["TITLE", "is_live", "DATE"], ascending=[True, True, False]
    ).copy()
    df.loc[df.duplicated(("TITLE", "ARTIST")), "flag"] = True
    return df


def _mark_matching_titles(
    df: pd.DataFrame,
    pattern: str,
    by: str | list[str],
    *,
    keep_first_when_all_match: bool,
) -> pd.DataFrame:
    df = df.copy()
    flagged: list[int] = []

    for _, group in df[~df["flag"]].groupby(by):
        if len(group) < 2:
            continue

        matches = group.index[group["TITLE"].str.contains(pattern, regex=True)].tolist()
        if len(matches) == len(group):
            matches = matches[1:] if keep_first_when_all_match else []
        flagged.extend(matches)

    df.loc[flagged, "flag"] = True
    return df


def mark_instrumentals(df: pd.DataFrame) -> pd.DataFrame:
    """同じグループ内のインストゥルメンタル版にフラグを立てる。"""
    return _mark_matching_titles(
        df,
        INSTRUMENTAL_PATTERN,
        "title_group",
        keep_first_when_all_match=False,
    )


def mark_live_versions(df: pd.DataFrame) -> pd.DataFrame:
    """同じグループ・アーティスト内のライブ版にフラグを立てる。"""
    return _mark_matching_titles(
        df,
        LIVE_TITLE_PATTERN,
        ["title_group", "ARTIST"],
        keep_first_when_all_match=True,
    )


def mark_alternate_versions(df: pd.DataFrame) -> pd.DataFrame:
    """TVサイズ、リミックスなどの別バージョンにフラグを立てる。"""
    return _mark_matching_titles(
        df,
        ALTERNATE_VERSION_PATTERN,
        ["title_group", "ARTIST"],
        keep_first_when_all_match=True,
    )


def mark_remastered(df: pd.DataFrame) -> pd.DataFrame:
    """リマスター版を識別する列を追加する。"""
    df = df.copy()
    df["is_remaster"] = (
        df["TITLE"].str.contains(REMASTER_PATTERN, regex=True).astype(int)
    )
    return df


def sort_for_deduplication(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(DEDUP_SORT_COLUMNS, ascending=DEDUP_SORT_ASCENDING)


def mark_duplicate_trans_titles(df: pd.DataFrame) -> pd.DataFrame:
    """変換後タイトルとアーティストが同じ曲にフラグを立てる。"""
    df = sort_for_deduplication(df).copy()
    df.loc[df.duplicated(("trans_title", "ARTIST")), "flag"] = True
    return sort_for_deduplication(df)


def mark_remaining_live_versions(df: pd.DataFrame) -> pd.DataFrame:
    """グループ内に残ったライブ版にフラグを立てる。"""
    df = df.copy()
    flagged: list[int] = []

    for _, group in df[~df["flag"]].groupby(["title_group", "ARTIST"]):
        if len(group) < 2:
            continue

        matches = group.index[group["is_live"] == 1].tolist()
        if len(matches) == len(group):
            matches = matches[1:]
        flagged.extend(matches)

    df.loc[flagged, "flag"] = True
    return df


def deduplicate(tracks: Sequence[Track]) -> pd.DataFrame:
    """曲データに重複判定パイプラインを適用する。"""
    df = build_dataframe(tracks)
    df = normalize_tracks(df)
    df = add_title_groups(df)
    df = mark_initial_flags(df)
    df = mark_duplicate_titles(df)
    df = df.sort_values(["title_group", "DATE"], ascending=[True, False])
    df = mark_instrumentals(df)
    df = mark_live_versions(df)
    df = mark_alternate_versions(df)
    df = mark_remastered(df)
    df = mark_duplicate_trans_titles(df)
    return mark_remaining_live_versions(df)
