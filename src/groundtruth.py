"""Maps the Mendeley dataset's ground-truth labels onto our taxonomy.

Two jobs:

1. **Scoring.** Defines what a correct extraction looks like for each labelled clip, so
   `score.py` can put a number on Pegasus the moment a key exists.

2. **Simulating extraction.** Lets the whole pipeline run end-to-end on the real 40 clips
   today, with no API key. That is not a substitute for measuring Pegasus — it is a
   rehearsal that proves everything *downstream* of extraction works on the real file set,
   so when the key lands the only unknown left is the model itself.

The critical asymmetry: **a safe clip should produce zero events.** The dataset's safe
classes are the negative set, and false positives on them are the failure mode that would
make this tool useless in a real plant — an alert firing on ordinary work is how people
learn to ignore alerts.
"""

from __future__ import annotations

from typing import Any

# label -> what a correct extraction should contain. None means "expect no events".
EXPECTED: dict[str, dict[str, Any] | None] = {
    "safe_walkway_violation": {
        "hazard_type": "vehicle_pedestrian_proximity",
        "actors": ["forklift", "pedestrian_worker"],
        "missing_controls": ["segregated_walkway", "floor_marking"],
        "proximity_band": "under_1m",
        "sif_potential": "high",
        "description": "Worker crossed a route used by powered equipment outside a marked walkway.",
        "counterfactual": "Had the operator not seen the worker, contact was plausible.",
    },
    "unauthorized_intervention": {
        "hazard_type": "energised_equipment",
        "actors": ["pedestrian_worker", "conveyor"],
        "missing_controls": ["lockout_tagout", "exclusion_zone"],
        "proximity_band": "contact",
        "sif_potential": "high",
        "description": "Worker reached into running equipment without isolating it.",
        "counterfactual": "An unexpected start or moving part would have caught the hand or arm.",
    },
    "opened_panel_cover": {
        "hazard_type": "unguarded_machinery",
        "actors": ["conveyor", "pedestrian_worker"],
        "missing_controls": ["machine_guarding"],
        "proximity_band": "under_1m",
        "sif_potential": "moderate",
        "description": "Machine operated with an access panel left open.",
        "counterfactual": "Anyone passing close could have contacted an unguarded moving part.",
    },
    "carrying_overload_forklift": {
        "hazard_type": "suspended_load",
        "actors": ["forklift", "stacked_load"],
        "missing_controls": ["load_securing", "spotter_present"],
        "proximity_band": "1_to_3m",
        "sif_potential": "high",
        "description": "Forklift travelled with a load above safe height and unsecured.",
        "counterfactual": "A shift in the load would have dropped it into the travel path.",
    },
    # negative set — correct behaviour is to return nothing
    "safe_walkway": None,
    "authorized_intervention": None,
    "closed_panel_cover": None,
    "safe_carrying": None,
}


def simulate_extraction(label: str, clip_id: str, duration: float = 8.0) -> list[dict[str, Any]]:
    """What a perfect extractor would return for a clip with this label.

    Used only when TL_API_KEY is unset. It is a ceiling, not a prediction — real Pegasus
    output will be messier, and the gap between this and that is exactly what score.py
    measures.
    """
    spec = EXPECTED.get(label)
    if spec is None:
        return []
    return [
        {
            **spec,
            "id": f"{clip_id}-000",
            "start": 0.0,
            "end": round(duration, 1),
        }
    ]


def expected_hazard(label: str) -> str | None:
    spec = EXPECTED.get(label)
    return spec["hazard_type"] if spec else None


def is_negative(label: str) -> bool:
    """True when a correct extractor returns no events for this clip."""
    return EXPECTED.get(label) is None
