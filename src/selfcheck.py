"""Fast consistency checks. Run before touching anything.

    python src/selfcheck.py

These catch the class of bug that costs an hour at 11am and looks like nothing: a value in
groundtruth.py that isn't in the taxonomy, an enum in the Pegasus schema that drifted from
taxonomy.py, a fingerprint that silently collides. None of it needs a database or an API
key.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from extraction import EVENT_SCHEMA  # noqa: E402
from groundtruth import EXPECTED  # noqa: E402
from loader import fingerprint  # noqa: E402
from taxonomy import (  # noqa: E402
    ACTOR_TYPES,
    CONTROLS,
    HAZARD_TYPES,
    PROXIMITY_BANDS,
    PROXIMITY_ORDINAL,
    SIF_POTENTIAL,
    SIF_WEIGHT,
)

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        failures.append(f"{name}: {detail}")
        if detail:
            print(f"        {detail}")


print("taxonomy")
check("no duplicate values", all(
    len(x) == len(set(x))
    for x in (HAZARD_TYPES, ACTOR_TYPES, CONTROLS, PROXIMITY_BANDS, SIF_POTENTIAL)
))
check(
    "every SIF level is weighted",
    set(SIF_POTENTIAL) == set(SIF_WEIGHT),
    f"missing {set(SIF_POTENTIAL) ^ set(SIF_WEIGHT)}",
)
check(
    "proximity ordinals cover every band except not_applicable",
    set(PROXIMITY_BANDS) - set(PROXIMITY_ORDINAL) == {"not_applicable"},
    f"unmapped: {set(PROXIMITY_BANDS) - set(PROXIMITY_ORDINAL)}",
)
check(
    "proximity ordinals are closest-first",
    list(PROXIMITY_ORDINAL.values()) == sorted(PROXIMITY_ORDINAL.values()),
)

print("\npegasus schema")
props = EVENT_SCHEMA["$defs"]["Event"]["properties"]
for field, expected in [
    ("hazard_type", HAZARD_TYPES),
    ("proximity_band", PROXIMITY_BANDS),
    ("sif_potential", SIF_POTENTIAL),
]:
    check(f"{field} enum matches taxonomy", props[field]["enum"] == expected)
for field, expected in [("actors", ACTOR_TYPES), ("missing_controls", CONTROLS)]:
    check(f"{field} item enum matches taxonomy", props[field]["items"]["enum"] == expected)
check(
    "every property is required",
    set(props) == set(EVENT_SCHEMA["$defs"]["Event"]["required"]),
    "optional fields let the model silently omit them",
)
check("counterfactual is present", "counterfactual" in props, "this field IS the SIF judgement")

print("\nground truth mappings")
for label, spec in EXPECTED.items():
    if spec is None:
        continue
    bad = (
        [a for a in spec["actors"] if a not in ACTOR_TYPES]
        + [c for c in spec["missing_controls"] if c not in CONTROLS]
        + ([spec["hazard_type"]] if spec["hazard_type"] not in HAZARD_TYPES else [])
        + ([spec["sif_potential"]] if spec["sif_potential"] not in SIF_POTENTIAL else [])
        + ([spec["proximity_band"]] if spec["proximity_band"] not in PROXIMITY_BANDS else [])
    )
    check(f"{label} uses only taxonomy values", not bad, f"unknown: {bad}")
check(
    "4 positive and 4 negative classes",
    sum(v is None for v in EXPECTED.values()) == 4
    and sum(v is not None for v in EXPECTED.values()) == 4,
)

print("\nfingerprint")
base = {
    "hazard_type": "vehicle_pedestrian_proximity",
    "actors": ["forklift", "pedestrian_worker"],
    "missing_controls": ["segregated_walkway", "floor_marking"],
}
shuffled = {
    "hazard_type": "vehicle_pedestrian_proximity",
    "actors": ["pedestrian_worker", "forklift"],
    "missing_controls": ["floor_marking", "segregated_walkway"],
}
check("order independent", fingerprint(base) == fingerprint(shuffled))
check(
    "different hazard -> different fingerprint",
    fingerprint(base) != fingerprint({**base, "hazard_type": "suspended_load"}),
)
check(
    "different absent control -> different fingerprint",
    fingerprint(base) != fingerprint({**base, "missing_controls": ["segregated_walkway"]}),
)
check(
    "different actors -> different fingerprint",
    fingerprint(base) != fingerprint({**base, "actors": ["delivery_vehicle", "pedestrian_worker"]}),
)
check(
    "no collisions across the full taxonomy cross-product",
    len({
        fingerprint({"hazard_type": h, "actors": [a], "missing_controls": [c]})
        for h in HAZARD_TYPES for a in ACTOR_TYPES for c in CONTROLS
    }) == len(HAZARD_TYPES) * len(ACTOR_TYPES) * len(CONTROLS),
)

print("\nopenai layer")
from brief import SYSTEM, PatternBrief  # noqa: E402
from context import render  # noqa: E402

# With structured_output, Field(description=...) IS the instruction the model receives.
# An undescribed field doesn't error — it just quietly produces worse output.
undescribed = [
    n for n, f in PatternBrief.model_fields.items()
    if not (f.description or "").strip()
]
check("every brief field carries a description", not undescribed, f"missing: {undescribed}")
check(
    "confidence is constrained, not free text",
    "Literal" in str(PatternBrief.model_fields["confidence"].annotation),
)
check("prompt forbids blaming workers", "never" in SYSTEM.lower() and "blame" in SYSTEM.lower())
check(
    "prompt explains the proximity ordinal",
    "0 = contact" in SYSTEM,
    "without this the model reads a falling number as an improvement",
)
check(
    "prompt names the desensitisation signal",
    "desensitisation" in SYSTEM or "desensitization" in SYSTEM,
)

# render() runs against whatever the graph returns, including patterns with no proximity
# data at all. It must degrade, not raise.
try:
    render({})
    render({"occurrences": 0, "reports": 0, "severity": [], "trend": {}, "samples": []})
    render({"occurrences": 4, "reports": 0, "hazards": ["working_at_height"],
            "trend": {"n_was": 3, "n_now": 1, "px_was": None, "px_now": None,
                      "r_was": 0, "r_now": 0}})
    check("render survives empty and null-proximity contexts", True)
except Exception as exc:
    check("render survives empty and null-proximity contexts", False, f"{type(exc).__name__}: {exc}")

print()
if failures:
    print(f"{len(failures)} FAILED")
    sys.exit(1)
print("all checks passed")
