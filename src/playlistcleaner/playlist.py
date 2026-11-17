from pathlib import Path
from shutil import move

import pandas as pd

PRIORITY_COLUMNS = (
    "TITLE",
    "ARTIST",
    "ALBUM",
    "flag",
    "trans_title",
    "title_group",
)
DEFAULT_OUTPUT_DIR = Path("output")


def read_playlist(path: Path) -> list[str]:
    """M3U8 ファイルからコメント行と空行を除いた曲パスを読み取る。"""
    entries = pd.read_csv(
        path,
        sep="\t",
        header=None,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    )[0]
    entries = entries.str.strip()
    return entries[entries.ne("") & ~entries.str.startswith("#")].tolist()


def report_columns(df: pd.DataFrame) -> list[str]:
    """レポート出力用の列順を返す。"""
    return [
        *PRIORITY_COLUMNS,
        *(column for column in df.columns if column not in PRIORITY_COLUMNS),
    ]


def write_report(
    df: pd.DataFrame, playlist_path: Path, output_dir: Path = DEFAULT_OUTPUT_DIR
) -> Path:
    """判定結果の TSV を出力する。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"{playlist_path.stem}.tsv"
    ordered = df[report_columns(df)].sort_values(["title_group", "flag"])
    ordered.to_csv(report_path, sep="\t")
    return report_path


def archive_playlist(playlist_path: Path) -> Path:
    """元のプレイリストを OLD_ 付きの名前へ移動する。"""
    archived_path = playlist_path.with_name(f"OLD_{playlist_path.name}")
    move(playlist_path, archived_path)
    return archived_path


def write_playlist(df: pd.DataFrame, playlist_path: Path) -> None:
    """残す曲だけを元のプレイリストへ書き込む。"""
    df.sort_index().loc[~df["flag"], "path"].to_csv(
        playlist_path, index=False, header=False, sep="\t"
    )


def save_results(
    df: pd.DataFrame,
    playlist_path: Path,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> Path:
    """レポート出力、元プレイリストの退避、新プレイリストの書き込みを行う。"""
    report_path = write_report(df, playlist_path, output_dir=output_dir)
    archive_playlist(playlist_path)
    write_playlist(df, playlist_path)
    return report_path
