from mutagen.flac import FLAC
from mutagen import File
from sys import argv
import pandas as pd
from pathlib import Path
from os.path import relpath
from unicodedata import normalize
import re

import numpy as np


def get_info(path, m3u8_path):
    path = Path(path)
    audio = File(path)

    info_dict = {k: v for k, v in audio.tags}
    info_dict["has_jacket"] = len(audio.pictures) > 0
    info_dict["path"] = str(relpath(path, m3u8_path.parent))
    return info_dict


def normalizer(input_str):
    input_str = normalize("NFKC", input_str)
    input_str = input_str.lower()
    input_str = re.sub("[-\/\\^$*+?.|'~\"・]", " ", input_str)
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
    files = files.values.tolist()  # [:30]

    lst = [get_info(path, playlist) for path in files]
    df = pd.DataFrame(lst)
    df["ARTIST"] = df["ARTIST"].map(normalizer)
    df["TITLE"] = df["TITLE"].map(normalizer)
    df["ALBUM"] = df["ALBUM"].map(normalizer)
    df.loc[df["DATE"].isna(), "DATE"] = "0000-00-00"
    df = df.sort_values(["TITLE", "DATE"], ascending=[True, False])

    # trans_title, ARTISTが同じ場合は最新のもののみ残してDrop
    df = df.drop_duplicates(("TITLE", "ARTIST"))

    # グループ分け用にタイトルを変形
    df["trans_title"] = df["TITLE"]
    df["trans_title"] = df["trans_title"].str.replace("\(.*\)", "", regex=True)
    df["trans_title"] = df["trans_title"].str.replace("\[.*\]", "", regex=True)
    df["trans_title"] = df["trans_title"].str.replace("{.*}", "", regex=True)
    df["trans_title"] = df["trans_title"].str.replace(" ", "")

    # 変形タイトルでグループ化
    df["partial_title"] = None
    while df["partial_title"].isna().any():
        title = df[df["partial_title"].isna()].iloc[0]["trans_title"]
        regex = "^" + title
        df.loc[df["trans_title"].str.match(regex), "partial_title"] = title

    # アーティスト、タイトルグループごとに1曲選択
    lst = []
    for (partial_title, _), df_title in df.groupby(["partial_title", "ARTIST"]):
        df_title = df_title.sort_values(["TITLE", "DATE"], ascending=[True, False])
        df_title = df_title.drop_duplicates("TITLE")
        df_title["score"] = np.arange(len(df_title))

        # partial_titleにinstらしき文字が入っていた場合他の候補を確認
        regex = (
            "instrumental|without|backing track|karaoke|inst|カラオケ|off vocal|vocalless"
        )
        if re.findall(regex, partial_title):
            pattern = re.sub(regex, "", partial_title)
            pattern = re.sub(" $", "", pattern)
            pattern = re.sub("^ ", "", pattern)
            pattern = "^" + pattern

            if (
                df.loc[df["partial_title"] != partial_title, "TITLE"]
                .str.findall(pattern)
                .any()
            ):
                continue

        # インスト版の優先度を下げる
        df_title.loc[df_title["TITLE"].str.findall(regex).astype(bool), "score"] += 100

        # short 版の優先度を下げる
        regex = (
            "live|tv|short|single|remix|mix|wo|edit|ver|style|another|version|recording"
        )
        df_title.loc[df_title["TITLE"].str.findall(regex).astype(bool), "score"] += 1

        # COME ALONG, live盤 の優先度を下げる
        regex = "come along|live"
        df_title.loc[df_title["ALBUM"].str.findall(regex).astype(bool), "score"] += 10

        # remaster 以外の優先度を下げる
        regex = "remaster"
        df_title.loc[df_title["TITLE"].str.findall(regex).astype(bool), "score"] -= 1

        # score 順に並び替えて、最初のindexを取得
        df_title = df_title.sort_values("score")

        # score最小のindexを取得
        lst.append(df_title.index.values.tolist()[0])

    # debug
    df["flag"] = False
    df.loc[lst, "flag"] = True
    df.to_csv("test.csv")

    df.loc[df["flag"], "path"].to_csv(
        playlist.parent / "test.m3u8", index=False, header=False
    )
