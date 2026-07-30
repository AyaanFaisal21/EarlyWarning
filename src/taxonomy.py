"""Controlled vocabularies.

Everything the model extracts is constrained to these enums. That is deliberate and it is
the single most important design decision in the project:

  - Free-text extraction produces "forklift near pedestrian" and "pedestrian close to a
    forklift" as two distinct things, which destroys cross-video grouping.
  - Enum-constrained extraction turns the problem from open generation into classification.
    Fingerprints become exact-match, entity resolution disappears, and clustering is a MERGE
    instead of an embedding threshold you tune under time pressure.

Add to these lists freely; just never let the model invent a value outside them.
"""

HAZARD_TYPES = [
    "vehicle_pedestrian_proximity",
    "suspended_load",
    "working_at_height",
    "unguarded_machinery",
    "slip_trip_hazard",
    "manual_handling",
    "confined_space_entry",
    "energised_equipment",
    "obstructed_egress",
    "line_of_fire",
]

ACTOR_TYPES = [
    "pedestrian_worker",
    "forklift",
    "pallet_jack",
    "overhead_crane",
    "delivery_vehicle",
    "ladder",
    "scissor_lift",
    "conveyor",
    "stacked_load",
]

# Controls whose ABSENCE is what makes a near-miss serious. Modelled as a first-class edge
# (:Event)-[:MISSING_CONTROL]->(:Control) so "what wasn't there" is directly queryable —
# absence is the whole point and it should not be buried in a text field.
CONTROLS = [
    "physical_barrier",
    "segregated_walkway",
    "spotter_present",
    "high_vis_ppe",
    "fall_arrest",
    "machine_guarding",
    "lockout_tagout",
    "load_securing",
    "audible_reversing_alarm",
    "floor_marking",
    "speed_limiter",
    "exclusion_zone",
]

# Ordinal, closest-first. We deliberately do NOT ask the model for a distance in metres:
# monocular video does not support that, and a float invites confident fabrication. Bands
# are what a human reviewer actually judges, and they are enough to detect drift.
PROXIMITY_BANDS = ["contact", "under_1m", "1_to_3m", "over_3m", "not_applicable"]

PROXIMITY_ORDINAL = {
    "contact": 0.0,
    "under_1m": 1.0,
    "1_to_3m": 2.0,
    "over_3m": 3.0,
    # not_applicable is excluded from drift maths rather than given a fake value
}

# The SIF (Serious Injury or Fatality) potential classification. This is the field the whole
# product exists to produce: modern EHS practice moved off counting near-misses precisely
# because they are not fungible, and onto judging which ones COULD have been fatal.
SIF_POTENTIAL = ["none", "low", "moderate", "high", "fatal"]

SIF_WEIGHT = {"none": 0.0, "low": 1.0, "moderate": 2.0, "high": 4.0, "fatal": 8.0}
