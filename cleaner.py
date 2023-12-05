import re
from os.path import relpath
from pathlib import Path
from shutil import move
from sys import argv
from unicodedata import normalize

import pandas as pd
import taglib
from numpy import roll
from tqdm import tqdm


def get_info(path, m3u8_path):
    path, m3u8_path = Path(path), Path(m3u8_path)
    if not path.is_absolute():
        path = (m3u8_path.parent / path).resolve(strict=True)

    with taglib.File(path, save_on_exit=False) as song:
        tags = song.tags

    info_dict = {k: v[0] for k, v in tags.items()}
    info_dict["path"] = str(relpath(path, m3u8_path.parent))
    return info_dict


def normalizer(input_str):
    input_str = normalize("NFKC", input_str)
    input_str = input_str.lower()
    input_str = re.sub("[\/\\^$*+?.|'\"・,、。’]", " ", input_str)
    input_str = re.sub(" +", " ", input_str)
    input_str = re.sub(" $", "", input_str)
    input_str = re.sub("^ ", "", input_str)
    return input_str


if __name__ == "__main__":
    assert len(argv) > 1
    playlist = Path(argv[1])
    files = pd.read_csv(playlist, sep="\t", header=None)
    files = files[0]
    files = files[~files.str.match("^#")]
    files = files.values.tolist()

    lst = [get_info(path, playlist) for path in tqdm(files, desc="read music metadata")]
    df = pd.DataFrame(lst)
    df = df[~df[["ARTIST", "ALBUM"]].isna().all(axis=1)]
    df["ARTIST"] = df["ARTIST"].map(normalizer)
    df["TITLE"] = df["TITLE"].map(normalizer)
    df["ALBUM"] = df["ALBUM"].map(normalizer)
    df.loc[df["DATE"].isna(), "DATE"] = "0000-00-00"

    # COME ALONG, live盤フラグ列を追加する
    regex = "come along|live"
    df["is_live"] = df["ALBUM"].str.findall(regex).astype(bool).astype(int)

    # グループ分け用にタイトルを変形
    df["trans_title"] = df["TITLE"]

    # 括弧の入れ子は考えないものとする
    df["trans_title"] = df["trans_title"].str.replace("\(.*?\)", "", regex=True)
    df["trans_title"] = df["trans_title"].str.replace("\[.*?\]", "", regex=True)
    df["trans_title"] = df["trans_title"].str.replace("{.*?}", "", regex=True)
    df["trans_title"] = df["trans_title"].str.replace("\-.*?\-", "", regex=True)
    df["trans_title"] = df["trans_title"].str.replace("\~.*?\~", "", regex=True)
    df["trans_title"] = df["trans_title"].str.replace("-", "")
    df["trans_title"] = df["trans_title"].str.replace("~", "")
    df["trans_title"] = df["trans_title"].str.replace(" ", "")
    # input_str = [s for s in input_str.split("~") if s][0]

    # 変形タイトルでグループ化
    df = df.sort_values(["trans_title", "DATE"], ascending=[True, False])
    df["group_pattern"] = roll(df["trans_title"].values, 1)
    df["title_group"] = df.apply(
        lambda x: int(
            not bool(re.findall("^" + re.escape(x["group_pattern"]), x["trans_title"]))
        ),
        axis=1,
    ).cumsum()

    # 除外管理フラグを追加
    df["flag"] = False

    # アーティスト名が「ドラマCD」の場合除外
    df.loc[df["ARTIST"] == "ドラマCD", "flag"] = True

    # 優先度順に並び替える
    df = df.sort_values(["TITLE", "is_live", "DATE"], ascending=[True, True, False])

    # TITLE, ARTISTが同じ場合は最初のものだけ残してDrop対象へ
    df.loc[df.duplicated(("TITLE", "ARTIST")), "flag"] = True

    # 優先度順に並び替える
    df = df.sort_values(["title_group", "DATE"], ascending=[True, False])

    # instを除外
    lst = []
    for title_group, df_title in df[~df["flag"]].groupby("title_group"):
        if len(df_title) < 2:
            continue

        # inst検出キーワード
        regex = (
            "instrumental|without|backing|karaoke|inst|カラオケ|off vocal|vocalless|ヴォーカルレス"
        )

        # TITLEがキーワードに一致する場合を除外リストに追加
        lst_sub = df_title.loc[
            df_title["TITLE"].str.findall(regex).astype(bool)
        ].index.values.tolist()
        if len(lst_sub) == len(df_title):
            lst_sub = []
        lst += lst_sub

    # 除外リストを適用
    df.loc[lst, "flag"] = True

    # live版を除外
    lst = []
    for (title_group, _), df_title in df[~df["flag"]].groupby(
        ["title_group", "ARTIST"]
    ):
        if len(df_title) < 2:
            continue

        # 検出キーワード
        regex = "live|ライブ"

        # TITLEがキーワードに一致する場合を除外リストに追加
        lst_sub = df_title.loc[
            df_title["TITLE"].str.findall(regex).astype(bool)
        ].index.values.tolist()
        if len(lst_sub) == len(df_title):
            lst_sub = lst_sub[1:]
        lst += lst_sub

    # 除外リストを適用
    df.loc[lst, "flag"] = True

    # アレンジ、ショート版を除外
    lst = []
    for (title_group, _), df_title in df[~df["flag"]].groupby(
        ["title_group", "ARTIST"]
    ):
        if len(df_title) < 2:
            continue

        # 検出キーワード
        regex = "tv|short|single|remix|mix|wo|edit|ver|style|another|version|recording|ヴァージョン|reprise|バージョン|mode"

        # TITLEがキーワードに一致する場合を除外リストに追加
        lst_sub = df_title.loc[
            df_title["TITLE"].str.findall(regex).astype(bool)
        ].index.values.tolist()
        if len(lst_sub) == len(df_title):
            lst_sub = lst_sub[1:]
        lst += lst_sub

    # 除外リストを適用
    df.loc[lst, "flag"] = True

    # is_remaster 列を追加
    regex = "remaster|aufwachen"
    df["is_remaster"] = df["TITLE"].str.findall(regex).astype(bool).astype(int)

    # 優先度順に並び替える
    df = df.sort_values(
        ["trans_title", "flag", "is_remaster", "is_live", "DATE"],
        ascending=[True, True, False, True, False],
    )

    # 同じtrans_titleのものをDrop
    df.loc[df.duplicated(("trans_title", "ARTIST")), "flag"] = True

    # 優先度順に並び替える
    df = df.sort_values(
        ["trans_title", "flag", "is_remaster", "is_live", "DATE"],
        ascending=[True, True, False, True, False],
    )

    # 同じtitle_groupの内live版のものが残っていればDROP
    lst = []
    for (title_group, _), df_title in df[~df["flag"]].groupby(
        ["title_group", "ARTIST"]
    ):
        if len(df_title) < 2:
            continue

        # TITLEがキーワードに一致する場合を除外リストに追加
        lst_sub = df_title[df_title["is_live"] == 1].index.values.tolist()
        if len(lst_sub) == len(df_title):
            lst_sub = lst_sub[1:]
        lst += lst_sub

    # 除外リストを適用
    df.loc[lst, "flag"] = True

    # tsvファイルを保存
    priority_columns = [
        "TITLE",
        "ARTIST",
        "ALBUM",
        "flag",
        "trans_title",
        "title_group",
    ]
    columns = df.drop(columns=priority_columns).columns.values.tolist()
    columns = priority_columns + columns
    output = Path("output")
    output.mkdir(exist_ok=True, parents=True)
    df[columns].sort_values(["title_group", "flag"]).to_csv(
        output / f"{playlist.stem}.tsv", sep="\t"
    )

    # 古いplaylistをリネーム
    move(playlist, playlist.parent / f"OLD_{playlist.name}")

    # playlistを保存
    df.sort_index().loc[~df["flag"], "path"].to_csv(playlist, index=False, header=False, sep="\t")
