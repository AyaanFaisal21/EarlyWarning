"""Run the demo. One command, four beats, no live typing.

    python src/ingest.py --reset      # synthetic corpus (has the time axis)
    python src/demo.py                # or --pause to step through with Enter

Presenting from a script rather than the Neo4j browser is deliberate: at 4pm, on someone
else's projector, with a timer running, the failure mode is fumbling a query — not a bad
query. Everything below is a live read of the database; nothing is cached or hardcoded.

Beat 3 needs an honest time axis, which only the synthetic corpus has (the real clips carry
no per-clip timestamp). Run it against the synthetic corpus and be explicit about that.
"""

from __future__ import annotations

import os
import sys
import textwrap

sys.path.insert(0, os.path.dirname(__file__))

from loader import Graph  # noqa: E402

BOLD, DIM, RESET = "\033[1m", "\033[2m", "\033[0m"


def wrap(text: str, indent: str = "    ") -> str:
    """Model-written prose is paragraph-length; unwrapped it runs off a projector."""
    return textwrap.fill(
        text or "", width=74, initial_indent=indent, subsequent_indent=indent
    )


def table(rows: list[dict], cols: list[tuple[str, str]]) -> str:
    if not rows:
        return "  (no rows)"
    widths = {
        k: max(len(h), *(len(str(r.get(k, ""))) for r in rows)) for k, h in cols
    }
    out = ["  " + "  ".join(h.ljust(widths[k]) for k, h in cols)]
    out.append("  " + "  ".join("-" * widths[k] for k, _ in cols))
    for r in rows:
        out.append("  " + "  ".join(str(r.get(k, "")).ljust(widths[k]) for k, _ in cols))
    return "\n".join(out)


def beat(n: int, title: str, say: str) -> None:
    print(f"\n{BOLD}{'=' * 74}\nBEAT {n} — {title}\n{'=' * 74}{RESET}")
    print(f"{DIM}{say}{RESET}\n")


def main() -> None:
    pause = "--pause" in sys.argv
    g = Graph()

    def step() -> None:
        if pause:
            input(f"\n{DIM}  [enter]{RESET}")

    try:
        total = g.run("MATCH (e:Event) RETURN count(e) AS n")[0]["n"]
        if not total:
            sys.exit("graph is empty — run: python src/ingest.py --reset")

        # ---------------------------------------------------------------- beat 1
        beat(
            1,
            "the inversion",
            "Reporting does not fail randomly. It collapses where severity climbs.",
        )
        rows = g.run("""
            MATCH (e:Event)
            OPTIONAL MATCH (e)-[:GENERATED]->(r:Report)
            WITH CASE WHEN e.sif_potential IN ['high','fatal']
                      THEN 'could have killed someone' ELSE 'minor potential' END AS band,
                 count(e) AS events, count(r) AS reports
            RETURN band, events, reports,
                   toString(toInteger(round(100.0*reports/events))) + '%' AS reported
            ORDER BY band
        """)
        print(table(rows, [("band", "SEVERITY"), ("events", "EVENTS"),
                           ("reports", "REPORTS"), ("reported", "REPORTED")]))
        step()

        # ---------------------------------------------------------------- beat 2
        beat(
            2,
            "frequency is the wrong ranking",
            "The most common hazard here is the least important one. That is why counting "
            "near-misses failed as a strategy.",
        )
        rows = g.run("""
            MATCH (p:Pattern)<-[:INSTANCE_OF]-(e:Event)
            OPTIONAL MATCH (e)-[:GENERATED]->(r:Report)
            WITH p, count(e) AS occurrences, count(r) AS reports,
                 sum(CASE e.sif_potential WHEN 'fatal' THEN 8.0 WHEN 'high' THEN 4.0
                     WHEN 'moderate' THEN 2.0 WHEN 'low' THEN 1.0 ELSE 0.0 END) AS w
            RETURN p.title AS pattern, occurrences, reports,
                   round(w * (1.0 - toFloat(reports)/occurrences), 1) AS unseen_risk
            ORDER BY unseen_risk DESC
        """)
        print(table(rows, [("pattern", "PATTERN"), ("occurrences", "SEEN"),
                           ("reports", "FILED"), ("unseen_risk", "UNSEEN RISK")]))
        if rows:
            print(f"\n{DIM}  Bottom row: most frequent hazard on site, least important thing "
                  f"on this list.{RESET}")

        # Only present once src/brief.py has run. Shown inline rather than as its own beat
        # because it is the same finding, explained — which is exactly OpenAI's job here.
        analysed = g.run("""
            MATCH (p:Pattern) WHERE p.root_cause_hypothesis IS NOT NULL
            MATCH (p)<-[:INSTANCE_OF]-(e:Event)
            OPTIONAL MATCH (e)-[:GENERATED]->(r:Report)
            WITH p, count(e) AS occ, count(r) AS rep,
                 sum(CASE e.sif_potential WHEN 'fatal' THEN 8.0 WHEN 'high' THEN 4.0
                     WHEN 'moderate' THEN 2.0 WHEN 'low' THEN 1.0 ELSE 0.0 END) AS w
            RETURN p.title AS title, p.root_cause_hypothesis AS why,
                   p.why_unreported AS unfiled, p.recommended_action AS action,
                   p.confidence AS confidence
            ORDER BY w * (1.0 - toFloat(rep)/occ) DESC LIMIT 1
        """)
        if analysed:
            a = analysed[0]
            print(f"\n{BOLD}  {a['title']}{RESET}  {DIM}(confidence: {a['confidence']}){RESET}")
            for label, text in [
                ("Why it keeps happening", a["why"]),
                ("Why nobody filed it", a["unfiled"]),
                ("Do this week", a["action"]),
            ]:
                print(f"\n  {BOLD}{label}.{RESET}")
                print(wrap(text))
        step()

        # ---------------------------------------------------------------- beat 3
        beat(
            3,
            "normalization of deviance, computed",
            "Vaughan named this studying Challenger: a practice drifts until it stops "
            "feeling wrong. It leaves a signature.",
        )
        rows = g.run("""
            MATCH (p:Pattern)<-[:INSTANCE_OF]-(e:Event)
            OPTIONAL MATCH (e)-[:GENERATED]->(r:Report)
            WITH p, e, (r IS NOT NULL) AS reported
            WITH p,
                 sum(CASE WHEN e.occurred_at >= datetime($split) THEN 1 ELSE 0 END) AS n_now,
                 sum(CASE WHEN e.occurred_at <  datetime($split) THEN 1 ELSE 0 END) AS n_was,
                 avg(CASE WHEN e.occurred_at >= datetime($split) THEN e.proximity_ord END) AS px_now,
                 avg(CASE WHEN e.occurred_at <  datetime($split) THEN e.proximity_ord END) AS px_was,
                 sum(CASE WHEN e.occurred_at >= datetime($split) AND reported THEN 1 ELSE 0 END) AS r_now,
                 sum(CASE WHEN e.occurred_at <  datetime($split) AND reported THEN 1 ELSE 0 END) AS r_was
            // Report rate must actually FALL, matching queries.cypher. Without this a
            // pattern that was never reported at all shows as '0% -> 0%', which reads as a
            // hole in the story rather than an example of it.
            WHERE n_was >= 3 AND n_now >= 3 AND px_now < px_was
              AND toFloat(r_now)/n_now < toFloat(r_was)/n_was
            RETURN p.title AS pattern,
                   toString(n_was) + ' -> ' + toString(n_now) AS events,
                   toString(round(px_was,2)) + ' -> ' + toString(round(px_now,2)) AS proximity,
                   toString(toInteger(round(100.0*r_was/n_was))) + '% -> ' +
                   toString(toInteger(round(100.0*r_now/n_now))) + '%' AS reported
            ORDER BY (px_was - px_now) * n_now DESC
        """, split="2026-06-29T00:00:00Z")
        print(table(rows, [("pattern", "PATTERN"), ("events", "EVENTS"),
                           ("proximity", "PROXIMITY"), ("reported", "REPORTED")]))
        print(f"\n{DIM}  Proximity falling means closer. Nobody decided to stop reporting —\n"
              f"  it stopped feeling like an event.{RESET}")
        step()

        # ---------------------------------------------------------------- beat 4
        beat(4, "the action", "End on something someone can go and do.")
        rows = g.run("""
            MATCH (c:Control)<-[:MISSING_CONTROL]-(e:Event)-[:INSTANCE_OF]->(p:Pattern)
            WHERE e.sif_potential IN ['high','fatal']
            RETURN c.name AS control, count(DISTINCT e) AS events,
                   count(DISTINCT p) AS patterns
            ORDER BY events DESC LIMIT 5
        """)
        print(table(rows, [("control", "INSTALL THIS CONTROL"),
                           ("events", "HIGH-POTENTIAL EVENTS"), ("patterns", "PATTERNS")]))
        if rows:
            t = rows[0]
            print(f"\n{DIM}  One control. {t['events']} events that could have killed someone, "
                  f"across {t['patterns']} situations nobody had connected.{RESET}")

        print(f"\n{BOLD}{'=' * 74}{RESET}")
        print("Normalization of deviance is a memory failure. It happens because nobody")
        print("compares today against two years ago. No human holds that. A graph does.\n")
    finally:
        g.close()


if __name__ == "__main__":
    main()
