"""Score extraction against the Mendeley ground-truth labels.

    python src/ingest.py --reset --videos data/*.mp4
    python src/score.py

This is the number that goes on stage. Without it the claim is "we built a pipeline"; with
it the claim is "we measured it on 40 labelled clips of real factory CCTV, and here is what
it got right and wrong."

Two metrics, and the second matters more than the first:

  DETECTION   did an unsafe clip produce an event, and did a safe clip produce none?
              Precision on the safe set is the one to watch. A tool that fires on ordinary
              work teaches people to ignore it, which is worse than no tool.

  HAZARD      given that it fired, did it pick the right hazard type? Wrong hazard means
              wrong fingerprint, which means wrong pattern, which means the clustering that
              the whole product rests on is quietly broken.

Run it with simulated extraction and you get a perfect score — that is expected and proves
only that the harness works. The number is meaningful once TL_API_KEY is set.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(__file__))

from groundtruth import expected_hazard, is_negative  # noqa: E402
from loader import Graph  # noqa: E402

# Threshold on SIF potential, not on event presence.
#
# Measured against real footage: Pegasus fires on safe clips too, but grades them 'low'
# (one safe-clip description literally reads "walking along a marked pathway"), while the
# unsafe counterpart came back 'high'. The severity grade is what discriminates, so that is
# what gets scored — which is also the product thesis: do not count near-misses, judge
# which ones could have hurt someone.
REPORTABLE = ("moderate", "high", "fatal")

EXTRACTED = """
MATCH (rec:Recording)
OPTIONAL MATCH (rec)-[:CONTAINS]->(e:Event)
WHERE e.sif_potential IN $reportable
OPTIONAL MATCH (e)-[:OF_TYPE]->(h:HazardType)
RETURN rec.id AS recording, collect(DISTINCT h.name) AS hazards, count(DISTINCT e) AS n
"""


def main() -> None:
    manifest_path = pathlib.Path("data/manifest.json")
    if not manifest_path.exists():
        sys.exit("no data/manifest.json — run src/fetch_footage.py first")

    manifest = json.loads(manifest_path.read_text())
    graph = Graph()
    try:
        rows = {r["recording"]: r for r in graph.run(EXTRACTED, reportable=list(REPORTABLE))}
    finally:
        graph.close()

    tp = fp = tn = fn = 0
    hazard_right = hazard_wrong = 0
    mistakes: list[str] = []

    for entry in manifest:
        label = entry["ground_truth_label"]
        row = rows.get(f"rec-{entry['filename']}")
        if row is None:
            continue
        fired = row["n"] > 0

        if is_negative(label):
            if fired:
                fp += 1
                mistakes.append(f"  FALSE ALARM  {entry['filename']:14s} {label} -> fired")
            else:
                tn += 1
        else:
            if fired:
                tp += 1
                want = expected_hazard(label)
                got = row["hazards"][0] if row["hazards"] else None
                if got == want:
                    hazard_right += 1
                else:
                    hazard_wrong += 1
                    mistakes.append(
                        f"  WRONG HAZARD {entry['filename']:14s} want {want}, got {got}"
                    )
            else:
                fn += 1
                mistakes.append(f"  MISSED       {entry['filename']:14s} {label}")

    scored = tp + fp + tn + fn
    if not scored:
        sys.exit("nothing scored — did ingest run over data/*.mp4?")

    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    haz = hazard_right / (hazard_right + hazard_wrong) if hazard_right + hazard_wrong else 0.0

    mode = "LIVE (TwelveLabs)" if os.environ.get("TL_API_KEY") else "SIMULATED (no API key)"
    print(f"extraction mode: {mode}")
    print(f"clips scored:    {scored}\n")

    print(f"DETECTION  (an event counts only at sif_potential in {list(REPORTABLE)})")
    print(f"  hazard found where one exists   {tp:3d}   (missed {fn})")
    print(f"  correctly silent on safe clips  {tn:3d}   (false alarms {fp})")
    print(f"  precision {prec:.0%}   recall {rec:.0%}   f1 {f1:.0%}\n")

    print("HAZARD TYPE")
    print(f"  correct {hazard_right}/{hazard_right + hazard_wrong}   ({haz:.0%})\n")

    if mistakes:
        print("MISTAKES")
        print("\n".join(mistakes[:15]))
        if len(mistakes) > 15:
            print(f"  ... and {len(mistakes) - 15} more")
    else:
        print("no mistakes")
        if mode.startswith("SIMULATED"):
            print("(expected — simulated extraction is derived from the labels themselves;")
            print(" this only confirms the harness works)")


if __name__ == "__main__":
    main()
