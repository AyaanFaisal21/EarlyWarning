"""Strands agent over the safety graph.

Tool design note: get_graph_schema exists because LLMs reliably invent labels and
relationship types that aren't in your database. Giving the model the real schema before it
writes Cypher is the difference between a demo that works and one that hallucinates
(:NearMiss) nodes you never created.

    python src/agent.py "what should the safety committee look at this month?"
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from strands import Agent, tool  # noqa: E402

from loader import Graph  # noqa: E402

_graph = Graph()

SYSTEM = """You are a workplace safety analyst working from camera-derived near-miss data.

Ground every claim in a query result. If the graph does not support an answer, say so rather
than estimating.

Two things you must get right, because they are the point of this system:

1. Rank by SIF potential, never by frequency. The most common hazard is rarely the most
   dangerous one. Counting near-misses is the strategy the industry abandoned.

2. An unreported pattern is more urgent than a reported one of equal severity. A hazard that
   generates reports is already visible to the organisation; one that generates none is
   drifting unseen.

When you describe a pattern, name the absent control. That is what someone can act on."""


@tool
def get_graph_schema() -> str:
    """Return the node labels, relationship types and properties actually present in the
    graph. Call this before writing any Cypher."""
    labels = _graph.run("CALL db.labels() YIELD label RETURN collect(label) AS l")
    rels = _graph.run(
        "CALL db.relationshipTypes() YIELD relationshipType "
        "RETURN collect(relationshipType) AS r"
    )
    props = _graph.run(
        "MATCH (e:Event) WITH e LIMIT 1 RETURN keys(e) AS event_properties"
    )
    return json.dumps(
        {
            "labels": labels[0]["l"] if labels else [],
            "relationships": rels[0]["r"] if rels else [],
            "event_properties": props[0]["event_properties"] if props else [],
        }
    )


@tool
def run_cypher(query: str) -> str:
    """Execute a read-only Cypher query and return rows as JSON.

    Use for counting, filtering, absence tests (NOT (e)-[:GENERATED]->(:Report)) and
    multi-hop traversal. Writes are rejected."""
    lowered = query.lower()
    if any(w in lowered for w in ("create", "merge", "delete", "set ", "remove", "drop")):
        return "Refused: read-only."
    try:
        return json.dumps(_graph.run(query), default=str)[:6000]
    except Exception as exc:  # surface the error so the model can repair its own query
        return f"Query failed: {exc}"


@tool
def deviance_drift(split_iso: str = "2026-06-29T00:00:00Z") -> str:
    """Find patterns showing normalization of deviance: occurrences rising while the safety
    margin shrinks and the report rate falls. split_iso divides the prior and recent
    windows."""
    cypher = """
    MATCH (p:Pattern)<-[:INSTANCE_OF]-(e:Event)
    OPTIONAL MATCH (e)-[:GENERATED]->(r:Report)
    WITH p, e, (r IS NOT NULL) AS reported
    WITH p,
         sum(CASE WHEN e.occurred_at >= datetime($split) THEN 1 ELSE 0 END) AS n_recent,
         sum(CASE WHEN e.occurred_at <  datetime($split) THEN 1 ELSE 0 END) AS n_prior,
         avg(CASE WHEN e.occurred_at >= datetime($split) THEN e.proximity_ord END) AS prox_recent,
         avg(CASE WHEN e.occurred_at <  datetime($split) THEN e.proximity_ord END) AS prox_prior,
         sum(CASE WHEN e.occurred_at >= datetime($split) AND reported THEN 1 ELSE 0 END) AS rep_recent,
         sum(CASE WHEN e.occurred_at <  datetime($split) AND reported THEN 1 ELSE 0 END) AS rep_prior
    WHERE n_prior >= 3 AND n_recent >= 3
    WITH p, n_prior, n_recent, prox_prior, prox_recent,
         toFloat(rep_prior)/n_prior AS rate_prior,
         toFloat(rep_recent)/n_recent AS rate_recent
    WHERE prox_recent < prox_prior AND rate_recent < rate_prior
    RETURN p.title AS pattern, n_prior, n_recent,
           round(prox_prior,2) AS proximity_before, round(prox_recent,2) AS proximity_now,
           round(rate_prior*100) AS reported_pct_before,
           round(rate_recent*100) AS reported_pct_now
    ORDER BY (prox_prior - prox_recent) * n_recent DESC
    """
    return json.dumps(_graph.run(cypher, split=split_iso), default=str)


@tool
def find_unreported_lookalikes(event_id: str) -> str:
    """Given an event that WAS reported, find similar events that were not, using Marengo
    embeddings. Use when the graph fingerprint may be too strict — near-identical events
    can get slightly different control assessments and land in separate patterns."""
    cypher = """
    MATCH (seed:Event {id: $event_id})
    CALL db.index.vector.queryNodes('event_embedding', 25, seed.embedding)
    YIELD node AS similar, score
    WHERE similar.id <> seed.id AND NOT (similar)-[:GENERATED]->(:Report)
    RETURN similar.id AS event, similar.description AS description,
           similar.sif_potential AS sif_potential, round(score,3) AS similarity
    ORDER BY similarity DESC LIMIT 10
    """
    return json.dumps(_graph.run(cypher, event_id=event_id), default=str)


def build_agent() -> Agent:
    from llm import build_agent as _build

    return _build(
        SYSTEM,
        tools=[
            get_graph_schema,
            run_cypher,
            deviance_drift,
            find_unreported_lookalikes,
        ],
    )


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or (
        "What should the safety committee look at this month, and why?"
    )
    try:
        print(build_agent()(question))
    finally:
        _graph.close()
