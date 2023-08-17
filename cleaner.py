from mutagen.flac import FLAC
from mutagen import File
from sys import argv
import pandas as pd
from pathlib import Path

def get_info(path):
    audio = File(path)
    info_dict = {k:v for k, v in audio.tags}
    info_dict["has_jacket"] = len(audio.pictures) > 0
    info_dict["path"] = str(path)
    return info_dict


if __name__=="__main__":
    assert len(argv) > 1
    playlist = Path(argv[1])
    musics = pd.read_csv(playlist, sep="\t", header=None, comment="^#")
    musics = musics[0].values.tolist()

    lst = [get_info(path)  for path in musics]
    df = pd.DataFrame(lst)
    print(df.head())
   
        