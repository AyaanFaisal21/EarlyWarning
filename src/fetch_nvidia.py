"""Pull synchronised camera views of one forklift/human near-miss run.

    python src/fetch_nvidia.py --list          # what runs are in the downloaded shard
    python src/fetch_nvidia.py --run run_12_seed_1669788307

NVIDIA PhysicalAI SDG-Warehouse (OpenMDW 1.1). Every clip is 10s of a *scripted* near miss
between a forklift and a person, filmed simultaneously by 5 ceiling and 5 eye-level
cameras. Files inside the shard are named by SHA hash; the scenario manifest maps each hash
back to an S3 path that encodes its run and camera.

Why this source and not the CCTV set: here the ground truth is unambiguous. Every run
contains a near miss by construction, so there is nothing to argue about when the extractor
fires. The CCTV set's labels encode human compliance — whether a worker stayed inside a
painted line — which is a different question from whether a machine did something
unexpected.

The ten synchronised views are the real prize. If the fingerprint groups by causal
structure, all ten collapse into one pattern. If it grouped by appearance, they would not —
a ceiling camera and a worker-height camera of the same instant look nothing alike. That is
a ground-truth test of the central claim, not an assertion about it.
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys
import tarfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHARD_DIR = ROOT / "data_nvidia" / "rgb" / "forklift_human_nearmiss"
MANIFEST = ROOT / "data_nvidia" / "metadata" / "manifests" / "manifest_nearmiss.json"
OUT = ROOT / "data_nvidia" / "clips"

S3_RE = re.compile(r"/nearmiss/(run_\d+_seed_\d+)/([^/]+)/rgb\.mp4$")


def hash_to_run() -> dict[str, tuple[str, str]]:
    """filename hash -> (run id, camera name)."""
    files = json.loads(MANIFEST.read_text())["files"]
    out = {}
    for fname, s3 in files.items():
        m = S3_RE.search(s3)
        if m:
            out[fname] = (m.group(1), m.group(2))
    return out


def camera_label(raw: str) -> str:
    """`_World_Cameras_ceiling_camera_Camera_03` -> `ceiling-03`."""
    kind = "ceiling" if "ceiling" in raw else "eye" if "eye" in raw else "cam"
    idx = raw.rsplit("_", 1)[-1]
    return f"{kind}-{idx}" if idx.isdigit() else f"{kind}-00"


def shards() -> list[pathlib.Path]:
    return sorted(SHARD_DIR.glob("*.tar"))


def index_shards(mapping: dict[str, tuple[str, str]]):
    """run id -> [(camera, tar path, member name)] for everything actually downloaded."""
    runs: dict[str, list[tuple[str, pathlib.Path, str]]] = collections.defaultdict(list)
    for tar_path in shards():
        with tarfile.open(tar_path) as tf:
            for member in tf.getnames():
                key = pathlib.Path(member).name
                if key in mapping:
                    run, cam = mapping[key]
                    runs[run].append((camera_label(cam), tar_path, member))
    return runs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", help="run id to extract; default is the most complete one")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--max-cameras", type=int, default=10)
    args = ap.parse_args()

    if not MANIFEST.exists():
        sys.exit(f"missing {MANIFEST} — download the scenario manifest first")
    if not shards():
        sys.exit(f"no shards in {SHARD_DIR} — download at least one .tar first")

    runs = index_shards(hash_to_run())
    if not runs:
        sys.exit("shard contained no files present in the near-miss manifest")

    ranked = sorted(runs.items(), key=lambda kv: -len(kv[1]))
    if args.list:
        print(f"{len(runs)} runs present in {len(shards())} downloaded shard(s)\n")
        for run, views in ranked[:20]:
            print(f"  {run:34s} {len(views):2d} cameras  "
                  f"{', '.join(sorted(c for c, _, _ in views)[:5])}...")
        return

    run = args.run or ranked[0][0]
    if run not in runs:
        sys.exit(f"{run} not in the downloaded shard; try --list")

    views = sorted(runs[run])[: args.max_cameras]
    dest = OUT / run
    dest.mkdir(parents=True, exist_ok=True)

    for cam, tar_path, member in views:
        with tarfile.open(tar_path) as tf:
            src = tf.extractfile(member)
            if src is None:
                continue
            target = dest / f"{cam}.mp4"
            target.write_bytes(src.read())
            print(f"  {cam:12s} {target.stat().st_size / 1e6:6.1f} MB  -> {target}")

    print(f"\n{len(views)} synchronised views of {run} -> {dest}")


if __name__ == "__main__":
    main()
