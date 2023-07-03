import argparse
import os
from sys import exit
import errno
from pathlib import Path
import ffmpeg
import configparser
import pysubs2
import warnings


SECOND_HALF_CHAPTER_NAMES = {"Part 2", "Part B"}


def main(args):
    video_dir = Path(args.dir)
    if not os.path.isdir(video_dir):
        print("video directory is not valid")
        exit(errno.ENOTDIR)
    video_files = [*video_dir.glob("*.mp4")] + [*video_dir.glob("*.mkv")]

    orig_sub_dir = video_dir / "subs_orig"
    if not orig_sub_dir.is_dir():
        print("could not find original subtitle subdirectory")
        exit(errno.ENOTDIR)
    orig_sub_files = [*orig_sub_dir.glob("*.srt")] + [*orig_sub_dir.glob("*.ass")]

    config = configparser.ConfigParser()
    config_file = orig_sub_dir / "retime.toml"
    if not config_file.exists():
        with open(config_file, "w") as conf:
            conf.write(
                """[offsets]
### folder/season-wide settings
main = 0
# 2nd_half = 0

### episode specific settings, e.g:
# main_1 = -1000
# 2nd_half_1 = -1000
"""
            )
    config.read(config_file)
    main_offset = int(config["offsets"]["main"])
    secondhalf_offset = (
        int(config["offsets"]["2nd_half"]) if "2nd_half" in config["offsets"] else None
    )

    new_sub_dir = video_dir / "subs"
    if not new_sub_dir.is_dir():
        if not new_sub_dir.exists():
            new_sub_dir.mkdir()
        else:
            print(f"{new_sub_dir} is not a directory")
            exit(errno.ENOTDIR)

    if len(video_files) != len(orig_sub_files):
        print(
            f"Video count does not match subtitle count ({len(video_files)} vs {len(orig_sub_files)})"
        )
        exit(1)

    # probably pointless, but eh
    video_files.sort()
    orig_sub_files.sort()

    for i in range(
        args.first
        if args.first is not None
        else len(video_files)  # do first N episodes, otherwise all
    ):
        orig_sub = orig_sub_files[i]
        vid = video_files[i]

        chapters = ffmpeg.probe(vid, show_chapters=None)["chapters"]
        for chapter in chapters:
            if "tags" in chapter and "title" in chapter["tags"]:
                chapter_title = chapter["tags"]["title"]
                if chapter_title in SECOND_HALF_CHAPTER_NAMES:
                    midpoint = round(float(chapter["start_time"]) * 1000)
                    break

        if secondhalf_offset and not midpoint:
            warnings.warn(
                f"Warning: No midpoint found for {vid} even though a 2nd half timing was specified"
            )

        episode_number = i + 1
        # load episode specific offsets if specifieed
        episode_main_offset = (
            int(config["offsets"][f"main_{episode_number}"])
            if f"{episode_number}_main" in config["offsets"]
            else None
        )
        episode_secondhalf_offset = (
            int(config["offsets"][f"2nd_half_{episode_number}"])
            if f"{episode_number}_2nd_half" in config["offsets"]
            else None
        )

        subs = pysubs2.load(orig_sub)
        for line in subs:
            if episode_secondhalf_offset and midpoint and line.start > midpoint:
                offset = episode_secondhalf_offset
            elif episode_main_offset:
                offset = episode_main_offset
            elif secondhalf_offset and midpoint and line.start > midpoint:
                offset = secondhalf_offset
            else:
                offset = main_offset

            line.start += offset
            line.end += offset

        # appending .ja so that MPV unambiguously knows they're JP subtitles
        new_sub = new_sub_dir / (vid.stem + ".ja" + orig_sub.suffix)
        subs.save(new_sub)
        print(f"Saved subtitle to {new_sub}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "dir",
        help="directory to work in",
        nargs="?",
        default=os.getcwd(),
    )

    parser.add_argument(
        "-f",
        "--first",
        type=int,
        metavar="N",
        help="only do the first N episodes (for testing)",
        default=None,
    )

    args = parser.parse_args()
    main(args)
