"""Find field footage that resembles a confirmed near miss.

    python src/match_reference.py              # rank field events by reference similarity
    python src/match_reference.py --top 5      # show the closest reference match for each

Nothing here is trained. Two corpora sit in one graph:

  reference  NVIDIA PhysicalAI clips, where a near miss occurs by construction. Dense with
             positives, unambiguous, synthetic.
  field      real workplace CCTV, where positives are rare, visually subtle, and mostly
             absent because compliant work looks like compliant work.

The reference set is a library of what the thing you are hunting actually looks like. Every
field event is scored by how close it sits, in Marengo's 512-d space, to its nearest
reference event. High scorers are the frames a reviewer should watch first.

This is the one job the graph genuinely cannot do — it is a similarity question, not a set
operation — which is why the vector index exists at all.

Honest limits worth keeping in view:
  - the reference set is rendered, so a field clip can score low simply for looking real
  - a high score means "resembles a known near miss", never "is one"
  - it ranks a review queue; it does not decide anything
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from loader import Graph  # noqa: E402

# For each field event, its single nearest reference event.
#
# queryNodes returns global neighbours, so we over-fetch and filter to reference-source
# rows rather than asking for k=1 and hoping the nearest happens to be one.
NEAREST = """
MATCH (rec:Recording {source: 'field'})-[:CONTAINS]->(e:Event)
WHERE e.embedding IS NOT NULL
CALL db.index.vector.queryNodes('event_embedding', 40, e.embedding)
YIELD node AS cand, score
MATCH (refrec:Recording {source: 'reference'})-[:CONTAINS]->(cand)
WITH e, rec, cand, refrec, score
ORDER BY score DESC
WITH e, rec, collect({clip: refrec.id, desc: cand.description, score: score})[0] AS best
RETURN rec.id            AS field_clip,
       e.description     AS field_desc,
       e.sif_potential   AS field_sif,
       e.proximity_band  AS field_prox,
       best.clip         AS ref_clip,
       best.desc         AS ref_desc,
       round(best.score, 4) AS similarity
ORDER BY similarity DESC
"""

COUNTS = """
MATCH (r:Recording)
OPTIONAL MATCH (r)-[:CONTAINS]->(e:Event)
RETURN r.source AS source, count(DISTINCT r) AS clips, count(e) AS events
ORDER BY source
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()

    graph = Graph()
    try:
        print("corpora in the graph:")
        for row in graph.run(COUNTS):
            print(f"  {str(row['source']):10s} {row['clips']:3d} clips, {row['events']:3d} events")

        rows = graph.run(NEAREST)
        if not rows:
            sys.exit(
                "\nno matches — need both a 'reference' and a 'field' corpus with embeddings.\n"
                "  python src/ingest.py --videos data_nvidia/clips/*.mp4 --source reference"
            )

        print(f"\nfield events ranked by resemblance to a confirmed near miss "
              f"(top {min(args.top, len(rows))} of {len(rows)}):\n")
        for r in rows[: args.top]:
            print(f"  {r['similarity']}  {r['field_clip'].replace('rec-', '')}"
                  f"   [{r['field_sif']} / {r['field_prox']}]")
            print(f"      field : {(r['field_desc'] or '')[:88]}")
            print(f"      ref   : {(r['ref_desc'] or '')[:88]}")
            print()

        scores = [r["similarity"] for r in rows]
        print(f"similarity spread: {min(scores):.3f} – {max(scores):.3f}, "
              f"median {sorted(scores)[len(scores) // 2]:.3f}")
        print("A tight spread means the embedding is not separating these; treat the ranking")
        print("as weak evidence and say so.")
    finally:
        graph.close()


if __name__ == "__main__":
    main()
