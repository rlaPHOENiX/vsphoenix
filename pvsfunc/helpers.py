import os
import subprocess
from itertools import groupby
from operator import itemgetter
from typing import Iterable, List

from pymediainfo import MediaInfo


def fps_reset(file_path: str) -> str:
    """Remove container-set FPS to only have the encoded FPS."""
    video_tracks = [x for x in MediaInfo.parse(file_path).tracks if x.track_type == "Video"]
    if not video_tracks:
        raise Exception("File does not have a video track, removing container-set FPS isn't possible.")
    video_track = video_tracks[0]
    if video_track.original_frame_rate is None:
        # no container-set FPS to remove, return unchanged
        return file_path
    out_path = file_path + ".pfpsreset.mkv"
    if os.path.exists(out_path):
        # an fps reset was already run on this file, re-use
        # todo ; could be dangerous, user might just make a file named this :/
        return out_path
    if video_track.framerate_original_num and video_track.framerate_original_den:
        original_fps = "%s/%s" % (video_track.framerate_original_num, video_track.framerate_original_den)
    else:
        original_fps = video_track.original_frame_rate
    subprocess.check_output([
        "mkvmerge", "--output", out_path,
        "--default-duration", "%d:%sfps" % (video_track.track_id - 1, original_fps),
        file_path
    ], cwd=os.path.dirname(file_path))
    return out_path


def gcd(a, b):
    """Calculate the GCD (greatest common divisor); the highest number that evenly divides both width and height."""
    return a if b == 0 else gcd(b, a % b)


def calculate_aspect_ratio(width: int, height: int) -> str:
    """Calculate the aspect-ratio gcd string from resolution."""
    r = gcd(width, height)
    return "%d:%d" % (int(width / r), int(height / r))


def calculate_par(width: int, height: int, aspect_ratio_w: int, aspect_ratio_h: int) -> str:
    """Calculate the pixel-aspect-ratio string from resolution."""
    par_w = height * aspect_ratio_w
    par_h = width * aspect_ratio_h
    par_gcd = gcd(par_w, par_h)
    par_w = int(par_w / par_gcd)
    par_h = int(par_h / par_gcd)
    return "%d:%d" % (par_w, par_h)


def list_select_every(data: list, cycle: int, offsets: (set, Iterable[int]), inverse: bool = False) -> list:
    """
    Same as VapourSynth's core.std.SelectEvery but for generic list data, and inverse.
    Don't use this as a replacement to core.std.SelectEvery, this should only be used on generic list data.
    """
    if not isinstance(cycle, int) or cycle < 1:
        raise ValueError("Cycle must be an int greater than or equal to 1.")
    if not offsets:
        raise ValueError("Offsets must not be empty.")
    if not isinstance(offsets, set):
        offsets = set(offsets)
    if not isinstance(inverse, bool) and inverse not in (0, 1):
        raise ValueError("Inverse must be a bool or int bool.")

    if not data:
        return data

    return [x for n, x in enumerate(data) if (n % cycle in offsets) ^ inverse]


def group_by_int(data: List[int]) -> list:
    """
    Group a list of integers into sub-lists.
    e.g. [1,2,3,5,6,7,9]: [[1,2,3],[5,6,7],[9]]
    """
    for k, g in groupby(enumerate(data), lambda x: x[0] - x[1]):
        yield list(map(itemgetter(1), g))
