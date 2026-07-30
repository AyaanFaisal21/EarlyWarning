"""End-to-end ingest. Runs today with no API keys.

    python src/ingest.py            # synthetic corpus
    python src/ingest.py --videos data/*.mp4   # real, needs TL_API_KEY + TL_INDEX_ID
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from loader import Graph  # noqa: E402
from seed import CAMERAS, SITE, build_corpus  # noqa: E402

BOOTSTRAP = """
MERGE (s:Site {id: $site_id}) SET s.name = $site_name
WITH s
UNWIND $cameras AS cam
  MERGE (c:Camera {id: cam.id}) SET c.location = cam.location
  MERGE (s)-[:HAS_CAMERA]->(c)
"""

RECORDING = """
MATCH (c:Camera {id: $camera_id})
MERGE (r:Recording {id: $recording_id})
  ON CREATE SET r.tl_asset_id = $tl_asset_id
MERGE (c)-[:RECORDED]->(r)
"""

REPORT = """
MATCH (e:Event {id: $event_id})
MERGE (r:Report {id: $report_id})
  SET r.filed_at = datetime($filed_at), r.filed_by_role = $filed_by_role
MERGE (e)-[:GENERATED]->(r)
"""


def ingest_synthetic(graph: Graph) -> None:
    events, reports = build_corpus()

    graph.run(
        BOOTSTRAP, site_id=SITE["id"], site_name=SITE["name"], cameras=CAMERAS
    )

    for rec_id in {e["recording_id"] for e in events}:
        camera_id = "-".join(rec_id.split("-")[1:3])
        graph.run(
            RECORDING,
            camera_id=camera_id,
            recording_id=rec_id,
            tl_asset_id=f"mock-{rec_id}",
        )

    graph.load_events(events)

    for rep in reports:
        graph.run(
            REPORT,
            event_id=rep["event_id"],
            report_id=rep["id"],
            filed_at=rep["filed_at"],
            filed_by_role=rep["filed_by_role"],
        )

    print(f"loaded {len(events)} events, {len(reports)} reports")
    severe = [e for e in events if e["sif_potential"] in ("high", "fatal")]
    minor = [e for e in events if e["sif_potential"] not in ("high", "fatal")]
    print(
        f"  could have killed someone: {len(severe):3d} events, "
        f"{sum(e['reported'] for e in severe) / len(severe):.0%} reported"
    )
    print(
        f"  minor potential:           {len(minor):3d} events, "
        f"{sum(e['reported'] for e in minor) / len(minor):.0%} reported"
    )


def _manifest(paths: list[str]) -> dict[str, str]:
    """filename -> ground-truth label, if data/manifest.json is present."""
    mpath = os.path.join(os.path.dirname(paths[0]) or ".", "manifest.json")
    if not os.path.exists(mpath):
        return {}
    with open(mpath) as fh:
        return {m["filename"]: m["ground_truth_label"] for m in json.load(fh)}


def ingest_videos(graph: Graph, paths: list[str]) -> None:
    """Ingest real clips.

    With TL_API_KEY set this uploads, indexes and runs Pegasus. Without it, and with a
    manifest present, it simulates extraction from the ground-truth labels so the full
    pipeline can be rehearsed on the real file set today.

    NOTE ON TIME: the Mendeley clips carry no per-clip timestamp, so occurred_at is
    ASSIGNED here — spread evenly across 12 weeks — purely to give the drift query an axis
    to work on. Drift results over real clips are therefore not a real temporal finding and
    must not be presented as one. Beat 3 of the demo belongs to the synthetic corpus, which
    has an honest time dimension by construction.
    """
    from extraction import embed_segment, ensure_index, extract_events, upload_and_index
    from groundtruth import simulate_extraction

    live = bool(os.environ.get("TL_API_KEY"))
    labels = _manifest(paths)
    if not live:
        print("TL_API_KEY unset — simulating extraction from ground-truth labels")
        if not labels:
            print("  (no manifest found; nothing to simulate)")
            return

    index_id = ensure_index() if live else ""
    graph.run(BOOTSTRAP, site_id=SITE["id"], site_name=SITE["name"], cameras=CAMERAS)

    base = datetime(2026, 5, 4, 8, 0, 0)
    step = timedelta(weeks=12) / max(len(paths), 1)

    for n, path in enumerate(paths):
        name = os.path.basename(path)
        rec_id = f"rec-{name}"

        if live:
            print(f"indexing {name} ...")
            asset_id = upload_and_index(path, index_id)
            events = extract_events(asset_id)
        else:
            asset_id = f"sim-{name}"
            events = simulate_extraction(labels.get(name, ""), rec_id)

        graph.run(
            RECORDING,
            camera_id=CAMERAS[0]["id"],
            recording_id=rec_id,
            tl_asset_id=asset_id,
        )

        for i, ev in enumerate(events):
            ev["id"] = f"{rec_id}-{i:03d}"
            ev["recording_id"] = rec_id
            ev["occurred_at"] = (base + step * n).isoformat()
            ev["embedding"] = embed_segment(asset_id, ev["start"], ev["end"])
        if events:
            graph.load_events(events)
        print(f"  {name:16s} {labels.get(name, '?'):28s} {len(events)} events")

    total = graph.run("MATCH (e:Event) RETURN count(e) AS n")[0]["n"]
    print(f"\n{total} events in graph from {len(paths)} clips")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos", nargs="*", help="video paths or URLs")
    ap.add_argument("--reset", action="store_true", help="wipe the graph first")
    args = ap.parse_args()

    graph = Graph()
    try:
        if args.reset:
            graph.run("MATCH (n) DETACH DELETE n")
            print("graph cleared")

        if args.videos:
            ingest_videos(graph, args.videos)
        else:
            ingest_synthetic(graph)
    finally:
        graph.close()


if __name__ == "__main__":
    main()
