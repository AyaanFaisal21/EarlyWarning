"""Pull a stratified sample of real workplace CCTV from Mendeley Data.

    python src/fetch_footage.py --per-class 5      # 40 clips, ~600 MB
    python src/fetch_footage.py --per-class 1      # 8 clips, smoke test

Dataset: "Video Dataset for Safe and Unsafe Behaviours"
  Oğuzhan Önal, Emre Dandıl — Bilecik Şeyh Edebali Üniversitesi
  DOI 10.17632/xjmtb22pff.1 — CC BY 4.0 (attribution required, commercial use permitted)

Real surveillance footage from a production facility in Eskişehir, Turkey, recorded
Nov–Dec 2022 by two IP cameras roughly 4 m above ground. 691 clips, 1920x1080, 24 fps,
H.264, 1–20 s each, 10 GB in total — hence the stratified sample.

Why this dataset and not a YouTube scrape: it is real CCTV at real camera height, it is
openly licensed, and — the part that matters — every unsafe class has a SAFE counterpart.
That gives ground truth for two things at once:

  1. Extraction accuracy. Does Pegasus flag the unsafe clips and leave the safe ones alone?
     That is a number you can put on stage instead of an assertion.

  2. The absence query, with both halves real. "Which conditions appear in unsafe clips and
     never in safe ones" is the set difference the whole product rests on, and here it can
     be checked against labels rather than asserted.

Writes data/manifest.json with the ground-truth label for every clip downloaded.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import ssl
import struct
import sys
import urllib.request

API = "https://data.mendeley.com/public-api/datasets/xjmtb22pff"


def _ssl_context() -> ssl.SSLContext | None:
    """python.org builds on macOS ship without the system trust store, so urllib fails cert
    verification where curl succeeds. certifi is the portable fix; if it isn't installed,
    say what to run rather than failing with a wall of traceback."""
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        print(
            "SSL verification will likely fail on macOS python.org builds.\n"
            "  pip install certifi\n"
            '  (or run "Install Certificates.command" from your Python install)',
            file=sys.stderr,
        )
        return None


CTX = _ssl_context()

# Prefix -> (label, is_unsafe, paired_class). Counts verified against the API listing.
CLASSES = {
    "0": ("safe_walkway_violation", True, "4"),      # 210 clips
    "1": ("unauthorized_intervention", True, "5"),   # 108
    "2": ("opened_panel_cover", True, "6"),          # 142
    "3": ("carrying_overload_forklift", True, "7"),  #  56
    "4": ("safe_walkway", False, "0"),               #  75
    "5": ("authorized_intervention", False, "1"),    #  38
    "6": ("closed_panel_cover", False, "2"),         #  32
    "7": ("safe_carrying", False, "3"),              #  30
}

CITATION = (
    "Önal, Oğuzhan; Dandıl, Emre (2024), 'Video Dataset for Safe and Unsafe Behaviours', "
    "Mendeley Data, V1, doi: 10.17632/xjmtb22pff.1 — CC BY 4.0"
)


# Mendeley 403s urllib's default User-Agent but serves curl fine, so send a real one.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    )
}


def _open(url: str, timeout: int):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=HEADERS), timeout=timeout, context=CTX
    )


def listing() -> list[dict]:
    with _open(API, 60) as resp:
        return json.load(resp)["files"]


def duration_sec(path: pathlib.Path) -> float | None:
    """Read duration from the MP4 mvhd atom.

    Needed because TwelveLabs rejects anything under 4 seconds
    ("video_duration_too_short"), and file size does not predict duration here — bitrates
    across this dataset vary by roughly 8x, so a 3 MB clip can be 10s while a 7 MB clip is
    3s. The only reliable way is to download and measure.
    """
    try:
        data = path.read_bytes()
    except OSError:
        return None
    i = data.find(b"mvhd")
    if i == -1:
        return None
    version = data[i + 4]
    try:
        if version == 0:
            timescale, dur = struct.unpack(">II", data[i + 16 : i + 24])
        else:
            (timescale,) = struct.unpack(">I", data[i + 24 : i + 28])
            (dur,) = struct.unpack(">Q", data[i + 28 : i + 36])
    except struct.error:
        return None
    return dur / timescale if timescale else None


def download(url: str, dest: pathlib.Path) -> None:
    """Stream to a .part file so an interrupted download never leaves a truncated MP4 that
    looks valid to the next run."""
    tmp = dest.with_suffix(dest.suffix + ".part")
    with _open(url, 300) as resp, tmp.open("wb") as fh:
        shutil.copyfileobj(resp, fh)
    tmp.rename(dest)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=5)
    ap.add_argument("--out", default="data")
    ap.add_argument("--dry-run", action="store_true")
    # TwelveLabs rejects anything under 4s with video_duration_too_short
    ap.add_argument("--min-seconds", type=float, default=4.0)
    args = ap.parse_args()

    out = pathlib.Path(args.out)
    out.mkdir(exist_ok=True)

    files = listing()
    buckets: dict[str, list[dict]] = {k: [] for k in CLASSES}
    for f in files:
        prefix = f["filename"].split("_")[0]
        if prefix in buckets:
            buckets[prefix].append(f)

    if args.dry_run:
        for prefix, items in buckets.items():
            print(f"  {CLASSES[prefix][0]:28s} {len(items):3d} candidates")
        return

    # Download smallest-first, but keep going until per_class clips clear min_seconds.
    # Anything shorter is deleted rather than left to fail at upload time.
    manifest = []
    for prefix, items in buckets.items():
        label, unsafe, pair = CLASSES[prefix]
        kept = 0
        for f in sorted(items, key=lambda x: x["size"]):
            if kept >= args.per_class:
                break
            dest = out / f["filename"]
            if not dest.exists():
                download(f["content_details"]["download_url"], dest)

            secs = duration_sec(dest)
            if secs is None or secs < args.min_seconds:
                dest.unlink(missing_ok=True)
                continue

            kept += 1
            print(f"  {label:28s} {f['filename']:14s} {secs:5.1f}s  {f['size'] / 1e6:5.1f} MB")
            manifest.append(
                {
                    "file": str(dest),
                    "filename": f["filename"],
                    "ground_truth_label": label,
                    "is_unsafe": unsafe,
                    "paired_class": CLASSES[pair][0],
                    "split": "test" if "_te" in f["filename"] else "train",
                    "size_bytes": f["size"],
                    "duration_sec": round(secs, 1),
                }
            )
        if kept < args.per_class:
            print(f"  ! {label}: only {kept}/{args.per_class} clips >= {args.min_seconds}s")

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (out / "CITATION.txt").write_text(CITATION + "\n")
    print(f"\n-> {out}/manifest.json  ({len(manifest)} clips)")
    print(f"-> {out}/CITATION.txt   (CC BY 4.0 requires attribution — keep this)")


if __name__ == "__main__":
    sys.exit(main())
