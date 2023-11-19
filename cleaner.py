from mutagen.flac import FLAC
from mutagen import File
from sys import argv
import pandas as pd
from pathlib import Path
from os.path import relpath
from unicodedata import normalize
import re


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
    input_str = re.sub("[-\/\\^$*+?.()|\[\]{}'~\"]", " ", input_str)
    input_str = re.sub(" +", " ", input_str)
    input_str = re.sub(" $", "", input_str)
    return input_str


if __name__ == "__main__":
    assert len(argv) > 1
    playlist = Path(argv[1])
    files = pd.read_csv(playlist, sep="\t", header=None)
    files = files[0]
    files = files[~files.str.match("^#")]
    files = files.values.tolist()[:30]

    lst = [get_info(path, playlist) for path in files]
    df = pd.DataFrame(lst).sort_values("TITLE")
    df["ARTIST"] = df["ARTIST"].map(normalizer)
    df["TITLE"] = df["TITLE"].map(normalizer)
    df["ALBUM"] = df["ALBUM"].map(normalizer)
    df.to_csv("test.csv")

    df["path"].to_csv(playlist.parent / "test.m3u8", index=False, header=False)
