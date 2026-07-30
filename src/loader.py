"""Neo4j loading and pattern fingerprinting."""

from __future__ import annotations

import hashlib
import os
from typing import Any

from neo4j import GraphDatabase

import env  # noqa: F401  — populates os.environ from .env before the reads below

URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
AUTH = (
    os.environ.get("NEO4J_USERNAME", "neo4j"),
    os.environ.get("NEO4J_PASSWORD", "hackathon2026"),
)


def fingerprint(event: dict[str, Any]) -> str:
    """-The grouping key — a subgraph signature, not a point in embedding space.

    This is the whole argument for using a graph here. Two events belong to the same pattern
    when they share a causal structure: same hazard, same absent controls, same actor types.
    Embedding similarity would instead group by appearance, so two unrelated failures in the
    same aisle collapse together while the same root cause at a second site never does.

    Sorting makes the key order-independent; the enum constraint on extraction makes it
    exact-match, so there is no similarity threshold to tune.
    """
    parts = [
        event["hazard_type"],
        ",".join(sorted(event.get("missing_controls", []))),
        ",".join(sorted(event.get("actors", []))),
    ]
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:16]


LOAD_EVENT = """
MERGE (e:Event {id: $id})
SET   e.occurred_at   = datetime($occurred_at),
      e.t_start       = $t_start,
      e.t_end         = $t_end,
      e.description   = $description,
      e.proximity_band= $proximity_band,
      e.proximity_ord = $proximity_ord,
      e.sif_potential = $sif_potential,
      e.counterfactual= $counterfactual,
      e.embedding     = $embedding

WITH e
MATCH (rec:Recording {id: $recording_id})
MERGE (rec)-[:CONTAINS]->(e)

WITH e
MERGE (h:HazardType {name: $hazard_type})
MERGE (e)-[:OF_TYPE]->(h)

WITH e
UNWIND $actors AS actor
  MERGE (a:Actor {name: actor})
  MERGE (e)-[:INVOLVED]->(a)

WITH DISTINCT e
UNWIND $missing_controls AS ctrl
  MERGE (c:Control {name: ctrl})
  MERGE (e)-[:MISSING_CONTROL]->(c)

WITH DISTINCT e
MERGE (p:Pattern {fingerprint: $fingerprint})
  ON CREATE SET p.id = randomUUID(), p.title = $pattern_title
MERGE (e)-[:INSTANCE_OF]->(p)
"""

REFRESH_PATTERNS = """
MATCH (p:Pattern)<-[:INSTANCE_OF]-(e:Event)
WITH p, count(e) AS n, min(e.occurred_at) AS first, max(e.occurred_at) AS last
SET p.count = n, p.first_seen = first, p.last_seen = last
"""


class Graph:
    def __init__(self, uri: str = URI, auth: tuple[str, str] = AUTH) -> None:
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self) -> None:
        self.driver.close()

    def run(self, cypher: str, **params: Any) -> list[dict[str, Any]]:
        with self.driver.session() as session:
            return [r.data() for r in session.run(cypher, **params)]

    def check_vector_dim(self, events: list[dict[str, Any]]) -> None:
        """Fail loudly if embeddings don't match the vector index.

        The reference implementation creates its index only after discovering the true
        dimension at runtime, because it varies by Marengo version — 2.7 was 1024, 3.0 is
        512. Neo4j does not reject a wrong-length vector on write; it just never returns it
        from the index. Silent, and you find out during the demo.
        """
        vec = next((e["embedding"] for e in events if e.get("embedding")), None)
        if not vec:
            return

        rows = self.run("""
            SHOW VECTOR INDEXES YIELD name, options
            WHERE name = 'event_embedding'
            RETURN options['indexConfig']['vector.dimensions'] AS dim
        """)
        if not rows or rows[0]["dim"] is None:
            return

        declared = int(rows[0]["dim"])
        if len(vec) != declared:
            raise RuntimeError(
                f"embedding dimension {len(vec)} != vector index dimension {declared}. "
                f"Vectors would be written but never returned by search. Fix schema.cypher "
                f"(`vector.dimensions`) and recreate the index."
            )

    def load_events(self, events: list[dict[str, Any]]) -> int:
        """Load extracted events. Idempotent — safe to re-run during a demo."""
        from taxonomy import PROXIMITY_ORDINAL

        self.check_vector_dim(events)

        with self.driver.session() as session:
            for ev in events:
                fp = fingerprint(ev)
                session.run(
                    LOAD_EVENT,
                    id=ev["id"],
                    recording_id=ev["recording_id"],
                    occurred_at=ev["occurred_at"],
                    t_start=ev["start"],
                    t_end=ev["end"],
                    description=ev["description"],
                    hazard_type=ev["hazard_type"],
                    actors=ev.get("actors", []),
                    missing_controls=ev.get("missing_controls", []),
                    proximity_band=ev["proximity_band"],
                    proximity_ord=PROXIMITY_ORDINAL.get(ev["proximity_band"]),
                    sif_potential=ev["sif_potential"],
                    counterfactual=ev["counterfactual"],
                    embedding=ev.get("embedding"),
                    fingerprint=fp,
                    pattern_title=_title(ev),
                )
            session.run(REFRESH_PATTERNS)
        return len(events)


def _title(event: dict[str, Any]) -> str:
    """Readable placeholder. agent.py can regenerate these with OpenAI from the subgraph,
    which reads far better on stage than a slug.

    Includes the lead actor because two patterns can share a hazard type and an absent
    control while being genuinely different situations — a forklift crossing a walkway is
    not a reversing trailer crossing one. Titling on hazard alone makes them indistinguishable
    in query output even though the fingerprints correctly differ.
    """
    hazard = event["hazard_type"].replace("_", " ")
    actors = sorted(a.replace("_", " ") for a in event.get("actors", []))
    lead = next((a for a in actors if a != "pedestrian worker"), actors[0] if actors else "")
    missing = event.get("missing_controls", [])
    head = f"{lead} — {hazard}" if lead else hazard
    return f"{head}, no {missing[0].replace('_', ' ')}" if missing else head
