"""TwelveLabs extraction: video -> structured near-miss events.

The JSON schema below is the core of the project. It does not ask "what happened" — it asks
"what nearly happened", which is the SIF-potential question and the thing a tally cannot
answer.

Two fields carry most of the weight:

  counterfactual   what would have happened had conditions been slightly different. This is
                   literally the textbook definition of SIF potential, asked of the model
                   directly rather than inferred downstream.
  missing_controls which safety control was absent. Absence is what makes a near-miss
                   serious, and it is what the graph can query and a vector index cannot.

Set TL_API_KEY to run for real; without it every function returns mock data so the whole
pipeline is exercisable today.
"""

from __future__ import annotations

import json
import os
from typing import Any

from taxonomy import (
    ACTOR_TYPES,
    CONTROLS,
    HAZARD_TYPES,
    PROXIMITY_BANDS,
    SIF_POTENTIAL,
)

PROMPT = """You are a safety officer reviewing factory CCTV, deciding which moments are
worth filing as near-miss reports.

A near miss is an EVENT, not a condition. Something has to have happened: a person and a
source of harm came into unintended proximity at a specific moment, because a normal
separation or barrier was absent or breached, and only timing, position or luck prevented
an injury.

Identify every situation where a person could plausibly have been injured had timing,
positioning, or conditions been slightly different. In particular:
  - a person on foot in or near the path of moving powered equipment
  - a person within reach of a moving part while a guard or access panel is open
  - a load carried, lifted, or moved over or beside a person
  - a person reaching into, leaning over, or contacting equipment that is running

Nothing bad will appear to happen — that is expected, and is exactly what makes these go
unreported. Report the situation anyway.

Only return an empty list if the clip shows no people, or no equipment in motion at all.

For each event you do report, you must name:
  - deviation: what departed from normal, expected operation at that moment
  - counterfactual: the small change in timing or position that would have caused injury

If you cannot name a specific deviation, do not report the event. Vague unease about the
general environment is not a deviation.

Do not estimate distances numerically. Choose a proximity band."""

EVENT_SCHEMA: dict[str, Any] = {
    "$defs": {
        "Event": {
            "type": "object",
            "properties": {
                "start": {"type": "number", "description": "start time in seconds"},
                "end": {"type": "number", "description": "end time in seconds"},
                "description": {
                    "type": "string",
                    "description": "one factual sentence, no speculation",
                },
                "hazard_type": {"type": "string", "enum": HAZARD_TYPES},
                "actors": {
                    "type": "array",
                    "items": {"type": "string", "enum": ACTOR_TYPES},
                },
                "missing_controls": {
                    "type": "array",
                    "items": {"type": "string", "enum": CONTROLS},
                    "description": "controls that should have been present but were not",
                },
                "proximity_band": {"type": "string", "enum": PROXIMITY_BANDS},
                "sif_potential": {
                    "type": "string",
                    "enum": SIF_POTENTIAL,
                    "description": "worst plausible outcome had conditions differed slightly",
                },
                "deviation": {
                    "type": "string",
                    "description": "what departed from normal, expected operation at this "
                    "moment. Required — an event with no nameable deviation is not a near "
                    "miss and should not be reported at all.",
                },
                "counterfactual": {
                    "type": "string",
                    "description": "the small change in timing or position that would have "
                    "caused an injury",
                },
            },
            "required": [
                "start",
                "end",
                "description",
                "hazard_type",
                "actors",
                "missing_controls",
                "proximity_band",
                "sif_potential",
                "deviation",
                "counterfactual",
            ],
        }
    },
    "type": "object",
    "properties": {"events": {"type": "array", "items": {"$ref": "#/$defs/Event"}}},
    "required": ["events"],
}


def _client():
    from twelvelabs import TwelveLabs

    return TwelveLabs(api_key=os.environ["TL_API_KEY"])


def ensure_index() -> str:
    """Return TL_INDEX_ID, creating the index if it isn't set.

    Saves a manual console step, and means a fresh machine only needs TL_API_KEY. The
    created id is printed — put it in .env to reuse the same index across runs rather than
    burning your 100-videos-per-index limit on duplicates.
    """
    existing = os.environ.get("TL_INDEX_ID")
    if existing:
        return existing

    client = _client()
    index = client.indexes.create(
        index_name=os.environ.get("TL_INDEX_NAME", "earlywarning"),
        models=[
            {"model_name": "marengo3.0", "model_options": ["visual", "audio"]},
            # Index creation accepts ONLY marengo3.0 / pegasus1.2 — asking for pegasus1.5
            # here returns 400 parameter_invalid. analyze() separately accepts
            # pegasus1.5, which is the version that does structured segmentation, so the
            # index is built on 1.2 and analysis requests 1.5. Verified against the live
            # API; the docs list both versions without saying which endpoint takes which.
            {"model_name": "pegasus1.2", "model_options": ["visual", "audio"]},
        ],
    )
    os.environ["TL_INDEX_ID"] = index.id
    print(f"created TwelveLabs index {index.id} — add to .env:\n  TL_INDEX_ID={index.id}")
    return index.id


def upload_and_index(path_or_url: str, index_id: str) -> str:
    """Upload a video and index it. Returns the ASSET id.

    Two-step flow — asset creation and indexing are separate, each with its own poll. This
    is the current API; older tutorials showing task.create() will not work.

    The two steps produce two DIFFERENT identifiers, and this matters: analyze() and
    embed() both key off the *asset* id, while search operates on the *indexed-asset* id.
    Passing the indexed-asset id to analyze returns
    404 resource_not_exists — which reads like the upload failed when in fact it succeeded.
    Returning the asset id keeps the common path correct.
    """
    import time

    client = _client()

    if path_or_url.startswith("http"):
        asset = client.assets.create(method="url", url=path_or_url)
    else:
        with open(path_or_url, "rb") as fh:
            asset = client.assets.create(method="direct", file=fh)

    while client.assets.retrieve(asset.id).status != "ready":
        time.sleep(3)

    indexed = client.indexes.indexed_assets.create(index_id=index_id, asset_id=asset.id)
    while (
        client.indexes.indexed_assets.retrieve(
            index_id=index_id, indexed_asset_id=indexed.id
        ).status
        != "ready"
    ):
        time.sleep(5)

    return asset.id


def extract_events(asset_id: str) -> list[dict[str, Any]]:
    """Run schema-constrained analysis over one indexed video."""
    if not os.environ.get("TL_API_KEY"):
        from seed import mock_events_for

        return mock_events_for(asset_id)

    from twelvelabs.types import (
        AnalyzePromptV2,
        SyncResponseFormat,
        VideoContext_AssetId,
    )

    client = _client()
    result = client.analyze(
        model_name="pegasus1.5",
        video=VideoContext_AssetId(asset_id=asset_id),
        prompt_v_2=AnalyzePromptV2(input_text=PROMPT),
        response_format=SyncResponseFormat(type="json_schema", json_schema=EVENT_SCHEMA),
    )
    return json.loads(result.data).get("events", []) if result.data else []


def embed_segment(asset_id: str, start: float, end: float) -> list[float]:
    """Marengo embedding for one clip. 512 dimensions — see schema.cypher.

    Powers the one job the graph genuinely cannot do: given a filed report, find visually
    similar events that were never filed.

    Video embedding lives on `embed.v_2`, NOT `embed.create` — the latter only accepts
    text, image and audio, so calling it with video kwargs raises TypeError. Verified by
    introspecting the installed SDK (twelvelabs 1.3.1). The older `embed.tasks.create_bulk`
    path is typed to `Marengo-retrieval-2.7`, which was sunset 2026-03-30; `embed.v_2` is
    the only route that accepts `marengo3.0`.
    """
    if not os.environ.get("TL_API_KEY"):
        from seed import mock_embedding

        return mock_embedding(f"{asset_id}:{start}")

    from twelvelabs.types import MediaSource, VideoInputRequest

    client = _client()
    res = client.embed.v_2.create(
        input_type="video",
        model_name="marengo3.0",
        video=VideoInputRequest(
            media_source=MediaSource(asset_id=asset_id),
            start_sec=start,
            end_sec=end,
            embedding_option=["visual", "audio"],
            embedding_scope=["clip"],
        ),
    )
    return _first_vector(res)


def _first_vector(res: Any) -> list[float]:
    """Pull the embedding out of the response.

    The exact attribute path can't be confirmed without a live key, so probe the plausible
    shapes and fail loudly with the real structure rather than silently returning None and
    poisoning the vector index with nulls.
    """
    for path in ("segments", "data", "embeddings"):
        items = getattr(res, path, None)
        if items:
            first = items[0]
            for attr in ("embedding", "float_", "values", "vector"):
                vec = getattr(first, attr, None)
                if vec:
                    return list(vec)
    raise RuntimeError(
        f"could not locate embedding in response; shape was {type(res).__name__} "
        f"with attrs {[a for a in dir(res) if not a.startswith('_')][:20]}"
    )
