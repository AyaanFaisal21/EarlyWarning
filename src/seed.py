"""Synthetic corpus — runs the whole pipeline with no API keys.

SYNTHETIC. Say so on stage. It is constructed to contain a specific, checkable structure so
you can verify the queries find what is actually there rather than eyeballing plausible
output:

  A  forklift/pedestrian, no segregated walkway
     The normalization-of-deviance case. Over 12 weeks occurrences rise 2/wk -> 6/wk, the
     proximity band degrades from 1_to_3m to under_1m/contact, and the report rate falls
     from ~50% to zero. Nobody decided to stop reporting; it stopped feeling like an event.

  B  suspended load, no exclusion zone
     Steady, high SIF potential, never once reported. The pure reporting gap.

  C  working at height, no fall arrest
     Rare, fatal potential, mostly reported. The system that already works.

  D  slip/trip hazard
     By far the most frequent, low potential, well reported. This one exists to prove that
     ranking by SIF potential is not ranking by count — which is the Heinrich critique made
     concrete and is worth pointing at during the demo.

Regenerate deterministically: `python src/seed.py`
"""

from __future__ import annotations

import hashlib
import math
import random
from datetime import datetime, timedelta
from typing import Any

SEED = 20260730
START = datetime(2026, 5, 4, 6, 0, 0)  # 12 weeks back from the event
SITE = {"id": "site-riverside", "name": "Riverside Distribution Centre"}
CAMERAS = [
    {"id": "cam-inbound", "location": "Inbound dock, aisles 1-4"},
    {"id": "cam-racking", "location": "High-bay racking, aisles 9-12"},
    {"id": "cam-yard", "location": "Yard and trailer park"},
]


def mock_embedding(key: str, cluster: str | None = None) -> list[float]:
    """Deterministic 512-d unit vector. Events sharing a cluster key land near each other so
    vector search behaves realistically against mock data."""
    base_seed = int(hashlib.sha1((cluster or key).encode()).hexdigest()[:8], 16)
    base = random.Random(base_seed)
    centre = [base.gauss(0, 1) for _ in range(512)]

    jitter = random.Random(int(hashlib.sha1(key.encode()).hexdigest()[:8], 16))
    vec = [c + jitter.gauss(0, 0.35) for c in centre]

    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _event(
    idx: int,
    week: int,
    camera: str,
    hazard: str,
    actors: list[str],
    missing: list[str],
    band: str,
    sif: str,
    desc: str,
    counterfactual: str,
    reported: bool,
) -> dict[str, Any]:
    rng = random.Random(SEED + idx)
    occurred = START + timedelta(
        weeks=week, days=rng.randint(0, 4), hours=rng.randint(1, 10)
    )
    cluster = f"{hazard}|{','.join(sorted(missing))}"
    return {
        "id": f"ev-{idx:04d}",
        "recording_id": f"rec-{camera}-w{week:02d}",
        "camera_id": camera,
        "occurred_at": occurred.isoformat(),
        "start": round(rng.uniform(10, 900), 1),
        "end": 0.0,  # filled below
        "description": desc,
        "hazard_type": hazard,
        "actors": actors,
        "missing_controls": missing,
        "proximity_band": band,
        "sif_potential": sif,
        "counterfactual": counterfactual,
        "reported": reported,
        "embedding": mock_embedding(f"ev-{idx:04d}", cluster),
    }


def build_corpus() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(SEED)
    events: list[dict[str, Any]] = []
    idx = 0

    # -- A: the drift case -------------------------------------------------------------
    for week in range(12):
        count = 2 + (week // 3)  # 2 -> 5 per week
        for _ in range(count):
            idx += 1
            # margin degrades as the practice normalises
            if week < 4:
                band = rng.choice(["1_to_3m", "1_to_3m", "over_3m"])
                sif = rng.choice(["moderate", "moderate", "low"])
            elif week < 8:
                band = rng.choice(["1_to_3m", "under_1m"])
                sif = rng.choice(["moderate", "high"])
            else:
                band = rng.choice(["under_1m", "under_1m", "contact"])
                sif = rng.choice(["high", "high", "fatal"])

            # report rate collapses even as severity climbs
            p_report = 0.5 if week < 4 else (0.15 if week < 8 else 0.0)
            events.append(
                _event(
                    idx,
                    week,
                    "cam-inbound",
                    "vehicle_pedestrian_proximity",
                    ["forklift", "pedestrian_worker"],
                    ["segregated_walkway", "floor_marking"],
                    band,
                    sif,
                    "Forklift crossed the inbound pedestrian route while a worker was walking it.",
                    "Had the worker stepped left, or the forklift not braked, contact was likely.",
                    rng.random() < p_report,
                )
            )

    # -- B: never reported -------------------------------------------------------------
    for week in range(12):
        for _ in range(rng.randint(1, 2)):
            idx += 1
            events.append(
                _event(
                    idx,
                    week,
                    "cam-racking",
                    "suspended_load",
                    ["overhead_crane", "stacked_load", "pedestrian_worker"],
                    ["exclusion_zone", "spotter_present"],
                    rng.choice(["under_1m", "1_to_3m"]),
                    rng.choice(["high", "fatal"]),
                    "Load traversed overhead while a worker remained within the swing path.",
                    "A sling failure or load swing at this moment would have struck the worker.",
                    False,
                )
            )

    # -- E: shares an absent control with A --------------------------------------------
    # Different hazard, different actors, same missing segregated_walkway. Exists so Q4 can
    # demonstrate its actual point: one control fix retires several distinct patterns. With
    # one pattern per control the query is correct but proves nothing.
    for week in range(12):
        if week % 2:
            continue
        idx += 1
        events.append(
            _event(
                idx,
                week,
                "cam-yard",
                "vehicle_pedestrian_proximity",
                ["delivery_vehicle", "pedestrian_worker"],
                ["segregated_walkway", "high_vis_ppe"],
                rng.choice(["under_1m", "1_to_3m"]),
                rng.choice(["high", "high", "fatal"]),
                "Reversing trailer crossed the yard walking route while a worker was on foot.",
                "With no walkway and no high-vis, the driver would not have seen a worker in the blind side.",
                rng.random() < 0.1,
            )
        )

    # -- C: rare, severe, mostly reported ----------------------------------------------
    for week in (1, 4, 7, 10):
        idx += 1
        events.append(
            _event(
                idx,
                week,
                "cam-racking",
                "working_at_height",
                ["scissor_lift", "pedestrian_worker"],
                ["fall_arrest"],
                "not_applicable",
                "fatal",
                "Worker leaned beyond the scissor-lift rail without a harness attached.",
                "A loss of balance at this height would very likely have been fatal.",
                rng.random() < 0.75,
            )
        )

    # -- D: frequent, minor, well reported ---------------------------------------------
    for week in range(12):
        for _ in range(rng.randint(2, 4)):
            idx += 1
            events.append(
                _event(
                    idx,
                    week,
                    "cam-yard",
                    "slip_trip_hazard",
                    ["pedestrian_worker"],
                    ["floor_marking"],
                    "not_applicable",
                    rng.choice(["low", "low", "moderate"]),
                    "Worker stepped over spilled granulate near the yard door.",
                    "A fall here would most likely have caused a sprain or bruise.",
                    rng.random() < 0.8,
                )
            )

    for ev in events:
        ev["end"] = round(ev["start"] + rng.uniform(3, 25), 1)

    reports = [
        {
            "id": f"rep-{ev['id']}",
            "event_id": ev["id"],
            "filed_at": ev["occurred_at"],
            "filed_by_role": rng.choice(["operative", "supervisor", "safety_officer"]),
        }
        for ev in events
        if ev["reported"]
    ]
    return events, reports


def mock_events_for(asset_id: str) -> list[dict[str, Any]]:
    """Stand-in for extraction.extract_events when TL_API_KEY is unset."""
    events, _ = build_corpus()
    return [e for e in events if e["recording_id"] == asset_id] or events[:3]


if __name__ == "__main__":
    import json
    import pathlib

    events, reports = build_corpus()
    out = pathlib.Path(__file__).parent.parent / "fixtures"
    out.mkdir(exist_ok=True)

    # embeddings are bulky and regenerable; keep the readable fixture small
    slim = [{k: v for k, v in e.items() if k != "embedding"} for e in events]
    (out / "events.json").write_text(json.dumps(slim, indent=2))
    (out / "reports.json").write_text(json.dumps(reports, indent=2))

    print(f"{len(events)} events, {len(reports)} reports -> {out}")
    print(f"overall reporting rate: {len(reports) / len(events):.0%}\n")

    # The overall rate is not the interesting number. This split is: reporting collapses
    # exactly where severity climbs, which is what the SIF literature predicts and what
    # makes 'count near-misses' a failed strategy.
    for band, label in (
        (("high", "fatal"), "could have killed someone"),
        (("none", "low", "moderate"), "minor potential          "),
    ):
        subset = [e for e in events if e["sif_potential"] in band]
        filed = [e for e in subset if e["reported"]]
        print(f"{label}: {len(subset):3d} events, {len(filed) / len(subset):>4.0%} reported")
