"""Serialise a pattern's subgraph into something a language model can reason over.

This module is the reason OpenAI is load-bearing rather than decorative. What gets sent is
not a video description and not a row from a table — it is *aggregated relational
structure*: severity distributions, proximity trends, report-rate trends, co-occurring
actors, absent controls, and the counterfactuals the extractor produced across dozens of
separate clips.

None of that exists before the graph is built. You could not assemble this prompt from raw
footage, from a vector index, or from any single video. That is what makes the model's
output reasoning *over the graph* rather than another pass of extraction.

No API key needed to run any of this — assembly is pure Cypher, and `render()` output is
inspectable, which is how you debug a bad answer without burning tokens guessing.
"""

from __future__ import annotations

from typing import Any

SUMMARY = """
MATCH (p:Pattern {fingerprint: $fp})<-[:INSTANCE_OF]-(e:Event)
OPTIONAL MATCH (e)-[:GENERATED]->(r:Report)
RETURN p.title AS current_title,
       count(DISTINCT e) AS occurrences,
       count(DISTINCT r) AS reports,
       min(e.occurred_at) AS first_seen,
       max(e.occurred_at) AS last_seen
"""

FACETS = """
MATCH (p:Pattern {fingerprint: $fp})<-[:INSTANCE_OF]-(e:Event)
OPTIONAL MATCH (e)-[:OF_TYPE]->(h:HazardType)
OPTIONAL MATCH (e)-[:INVOLVED]->(a:Actor)
OPTIONAL MATCH (e)-[:MISSING_CONTROL]->(c:Control)
RETURN collect(DISTINCT h.name) AS hazards,
       collect(DISTINCT a.name) AS actors,
       collect(DISTINCT c.name) AS absent_controls
"""

SEVERITY = """
MATCH (p:Pattern {fingerprint: $fp})<-[:INSTANCE_OF]-(e:Event)
RETURN e.sif_potential AS level, count(*) AS n ORDER BY n DESC
"""

TREND = """
MATCH (p:Pattern {fingerprint: $fp})<-[:INSTANCE_OF]-(e:Event)
OPTIONAL MATCH (e)-[:GENERATED]->(r:Report)
WITH e, (r IS NOT NULL) AS reported
RETURN sum(CASE WHEN e.occurred_at >= datetime($split) THEN 1 ELSE 0 END) AS n_now,
       sum(CASE WHEN e.occurred_at <  datetime($split) THEN 1 ELSE 0 END) AS n_was,
       avg(CASE WHEN e.occurred_at >= datetime($split) THEN e.proximity_ord END) AS px_now,
       avg(CASE WHEN e.occurred_at <  datetime($split) THEN e.proximity_ord END) AS px_was,
       sum(CASE WHEN e.occurred_at >= datetime($split) AND reported THEN 1 ELSE 0 END) AS r_now,
       sum(CASE WHEN e.occurred_at <  datetime($split) AND reported THEN 1 ELSE 0 END) AS r_was
"""

SAMPLES = """
MATCH (p:Pattern {fingerprint: $fp})<-[:INSTANCE_OF]-(e:Event)
RETURN DISTINCT e.description AS description, e.counterfactual AS counterfactual
LIMIT 4
"""

LOCATIONS = """
MATCH (p:Pattern {fingerprint: $fp})<-[:INSTANCE_OF]-(:Event)<-[:CONTAINS]-(:Recording)
      <-[:RECORDED]-(cam:Camera)
RETURN collect(DISTINCT cam.location) AS locations
"""

# Which other patterns share an absent control. This is the multi-hop bit — it lets the
# model observe that one missing control explains several situations, which is exactly the
# connection a human reviewing clips one at a time cannot make.
NEIGHBOURS = """
MATCH (p:Pattern {fingerprint: $fp})<-[:INSTANCE_OF]-(:Event)-[:MISSING_CONTROL]->(c:Control)
MATCH (c)<-[:MISSING_CONTROL]-(:Event)-[:INSTANCE_OF]->(other:Pattern)
WHERE other.fingerprint <> $fp
RETURN c.name AS shared_control, collect(DISTINCT other.title) AS also_affects
"""


def pattern_context(graph: Any, fingerprint: str, split: str = "2026-06-29T00:00:00Z") -> dict:
    """Assemble everything known about one pattern."""
    one = lambda q, **kw: (graph.run(q, fp=fingerprint, **kw) or [{}])[0]  # noqa: E731

    ctx: dict[str, Any] = {"fingerprint": fingerprint}
    ctx.update(one(SUMMARY))
    ctx.update(one(FACETS))
    ctx.update(one(LOCATIONS))
    ctx["severity"] = graph.run(SEVERITY, fp=fingerprint)
    ctx["trend"] = one(TREND, split=split)
    ctx["samples"] = graph.run(SAMPLES, fp=fingerprint)
    ctx["neighbours"] = graph.run(NEIGHBOURS, fp=fingerprint)
    return ctx


def render(ctx: dict) -> str:
    """Compact text form. Keep it dense — this is prompt payload, not a report."""
    occ = ctx.get("occurrences", 0) or 0
    rep = ctx.get("reports", 0) or 0
    lines = [
        f"HAZARD           {', '.join(ctx.get('hazards') or []) or 'unknown'}",
        f"ACTORS           {', '.join(ctx.get('actors') or [])}",
        f"ABSENT CONTROLS  {', '.join(ctx.get('absent_controls') or [])}",
        f"LOCATIONS        {', '.join(ctx.get('locations') or []) or 'unknown'}",
        f"OCCURRENCES      {occ} events, {rep} reported ({rep / occ:.0%})" if occ else "",
    ]

    sev = ctx.get("severity") or []
    if sev:
        lines.append(
            "SEVERITY MIX     "
            + ", ".join(f"{r['n']}x {r['level']}" for r in sev if r.get("level"))
        )

    t = ctx.get("trend") or {}
    if t.get("n_was") and t.get("n_now"):
        px_was, px_now = t.get("px_was"), t.get("px_now")
        if px_was is not None and px_now is not None:
            direction = "closer" if px_now < px_was else "further"
            lines.append(
                f"PROXIMITY TREND  {px_was:.2f} -> {px_now:.2f} ({direction}; "
                f"0=contact, 3=over 3m)"
            )
        lines.append(
            f"REPORTING TREND  {t['r_was'] / t['n_was']:.0%} -> {t['r_now'] / t['n_now']:.0%} "
            f"across {t['n_was']} then {t['n_now']} events"
        )

    for n in ctx.get("neighbours") or []:
        if n.get("also_affects"):
            lines.append(
                f"SHARED CONTROL   '{n['shared_control']}' is also absent in: "
                + "; ".join(n["also_affects"])
            )

    samples = ctx.get("samples") or []
    if samples:
        lines.append("\nOBSERVED (from separate clips):")
        for s in samples:
            lines.append(f"  - {s['description']}")
            if s.get("counterfactual"):
                lines.append(f"    what nearly happened: {s['counterfactual']}")

    return "\n".join(line for line in lines if line)


def all_patterns(graph: Any) -> list[dict]:
    """Patterns ranked by unseen risk — severity accumulated x fraction never reported."""
    return graph.run("""
        MATCH (p:Pattern)<-[:INSTANCE_OF]-(e:Event)
        OPTIONAL MATCH (e)-[:GENERATED]->(r:Report)
        WITH p, count(e) AS occurrences, count(r) AS reports,
             sum(CASE e.sif_potential WHEN 'fatal' THEN 8.0 WHEN 'high' THEN 4.0
                 WHEN 'moderate' THEN 2.0 WHEN 'low' THEN 1.0 ELSE 0.0 END) AS w
        RETURN p.fingerprint AS fingerprint, p.title AS title, occurrences, reports,
               round(w * (1.0 - toFloat(reports)/occurrences), 1) AS unseen_risk
        ORDER BY unseen_risk DESC
    """)
