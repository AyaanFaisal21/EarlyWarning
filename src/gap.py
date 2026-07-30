"""The reporting gap, straight from the graph. No model, no waiting.

    python3 src/gap.py

Built for demoing. src/agent.py can compose these queries itself from a plain-English
question, which is the more impressive thing — but it takes anywhere from 15 to 130
seconds depending on how many queries the model decides to run, and that variance is not
something you want in front of an audience. This runs the same Cypher directly and returns
in about a second, every time.

Show this live; show agent.py as code.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from loader import Graph  # noqa: E402

CORPUS = """
MATCH (r:Recording)
OPTIONAL MATCH (r)-[:CONTAINS]->(e:Event)
RETURN r.source AS source, count(DISTINCT r) AS clips, count(e) AS events
ORDER BY source
"""

# The headline: patterns the cameras saw repeatedly that produced no report at all.
# NOT (e)-[:GENERATED]->(:Report) is a negation over a relationship — the thing a vector
# index cannot express.
GAP = """
MATCH (p:Pattern)<-[:INSTANCE_OF]-(e:Event)
OPTIONAL MATCH (e)-[:GENERATED]->(r:Report)
WITH p, count(e) AS seen, count(r) AS filed,
     sum(CASE e.sif_potential WHEN 'fatal' THEN 1 WHEN 'high' THEN 1 ELSE 0 END) AS severe
WHERE filed = 0
RETURN p.title AS pattern, seen, severe
ORDER BY severe DESC, seen DESC LIMIT 6
"""

# Two hops: Control <- Event -> Pattern. One absent control, many distinct situations.
LEVERAGE = """
MATCH (c:Control)<-[:MISSING_CONTROL]-(e:Event)-[:INSTANCE_OF]->(p:Pattern)
WHERE e.sif_potential IN ['high', 'fatal']
RETURN c.name AS control, count(DISTINCT e) AS events, count(DISTINCT p) AS patterns
ORDER BY events DESC LIMIT 5
"""


def main() -> None:
    g = Graph()
    try:
        print("\n  CORPUS")
        for r in g.run(CORPUS):
            print(f"    {str(r['source']):10s} {r['clips']:3d} clips   {r['events']:3d} events")

        rows = g.run(GAP)
        total = g.run(
            "MATCH (p:Pattern)<-[:INSTANCE_OF]-(e:Event) "
            "OPTIONAL MATCH (e)-[:GENERATED]->(r:Report) "
            "WITH p, count(r) AS filed WHERE filed = 0 RETURN count(p) AS n"
        )[0]["n"]

        print(f"\n  PATTERNS THAT PRODUCED NO REPORT AT ALL — {total} of them")
        print(f"    {'pattern':58s} {'seen':>5s} {'severe':>7s}")
        for r in rows:
            print(f"    {r['pattern'][:58]:58s} {r['seen']:5d} {r['severe']:7d}")

        print("\n  ONE CONTROL, MANY SITUATIONS")
        print(f"    {'absent control':24s} {'events':>7s} {'patterns':>9s}")
        for r in g.run(LEVERAGE):
            print(f"    {r['control']:24s} {r['events']:7d} {r['patterns']:9d}")
        print()
    finally:
        g.close()


if __name__ == "__main__":
    main()
