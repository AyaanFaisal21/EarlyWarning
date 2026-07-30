"""Generate the safety committee brief — the OpenAI layer.

    python src/brief.py                  # inspect assembled prompts (no key needed)
    OPENAI_API_KEY=... python src/brief.py --write-titles

Without this the project outputs tables. With it, it outputs a document a safety manager
would act on. That is the difference between a query result and a product.

What the model is asked to do is deliberately *not* extraction — extraction already
happened, in Pegasus, per clip. Here the input is aggregated relational structure that only
exists after the graph is assembled: severity distributions across dozens of clips,
proximity and reporting trends over time, and which other patterns share an absent control.
The model reasons over the graph; it does not build it.

Three rules are enforced in the prompt because they are the failure modes that would make
the output worse than nothing:

  - Ground every claim in the supplied data. No invented plant details.
  - Never blame a worker. Name the missing control instead. Blame is precisely why 90% of
    near misses go unreported; a tool that reproduces it makes the problem worse.
  - Say when the evidence is thin. `confidence` is not decoration.

`--write-titles` pushes generated titles back onto the Pattern nodes, so `src/demo.py`
shows names a human wrote rather than slugs a formatter did.
"""

from __future__ import annotations

import os
import sys
from typing import Literal

sys.path.insert(0, os.path.dirname(__file__))

from pydantic import BaseModel, Field  # noqa: E402

from context import all_patterns, pattern_context, render  # noqa: E402
from loader import Graph  # noqa: E402

TOP_N = 3


class PatternBrief(BaseModel):
    """What the model must return for each pattern."""

    title: str = Field(
        description="How a safety manager would refer to this in a meeting. "
        "Max 60 characters. Concrete and specific to the location and equipment. "
        "Not a restatement of the hazard taxonomy."
    )
    root_cause_hypothesis: str = Field(
        description="Two or three sentences on why this keeps happening. Ground it only in "
        "the supplied data. Name the missing control, never a careless worker."
    )
    why_unreported: str = Field(
        description="One or two sentences on why these events are not being filed, using "
        "the reporting trend and severity mix as evidence."
    )
    recommended_action: str = Field(
        description="One concrete action someone could take this week and verify was done."
    )
    confidence: Literal["low", "medium", "high"] = Field(
        description="How well the supplied evidence supports the hypothesis. Use 'low' "
        "when the sample is small or the trend is weak."
    )


SYSTEM = """You are a workplace safety analyst writing for a site safety committee.

Your input is aggregated evidence from a near-miss graph built from CCTV: severity
distributions, proximity and reporting trends, absent controls, and observations drawn from
many separate clips.

Rules:
- Ground every claim in the data supplied. Do not invent plant details, shift patterns,
  names, or history you were not given.
- Never attribute cause to worker carelessness. Name the absent control or the conditions
  that made the error likely. Blame is why most near misses go unreported.
- If the evidence is thin, say so and set confidence to low.
- Proximity is an ordinal: 0 = contact, 1 = under 1m, 2 = 1-3m, 3 = over 3m. A falling
  number means events are getting closer, which is worse.
- Falling reporting alongside rising severity is a desensitisation signal, not an
  improvement. Treat it as urgent."""


def build_agent():
    from llm import build_agent as _build

    return _build(SYSTEM)


WRITE_BRIEF = """
MATCH (p:Pattern {fingerprint: $fp})
SET p.title = $title,
    p.root_cause_hypothesis = $hypothesis,
    p.why_unreported = $why_unreported,
    p.recommended_action = $action,
    p.confidence = $confidence
"""


def main() -> None:
    write = "--write-titles" in sys.argv
    live = bool(os.environ.get("OPENAI_API_KEY"))
    graph = Graph()

    try:
        patterns = all_patterns(graph)
        if not patterns:
            sys.exit("graph is empty — run: python src/ingest.py --reset")

        if not live:
            print("OPENAI_API_KEY unset — showing the prompts that would be sent.\n"
                  "Everything below is assembled from the graph; only the reasoning step\n"
                  "needs a key.\n")
            for p in patterns[:TOP_N]:
                print("=" * 74)
                print(f"{p['title']}   (unseen risk {p['unseen_risk']})")
                print("=" * 74)
                print(render(pattern_context(graph, p["fingerprint"])))
                print()
            return

        from llm import ask, model_id

        agent = build_agent()
        results = []
        print(f"reasoning with {model_id()} over {min(TOP_N, len(patterns))} patterns...\n")

        for p in patterns[:TOP_N]:
            ctx = pattern_context(graph, p["fingerprint"])
            prompt = (
                f"Analyse this recurring near-miss pattern.\n\n{render(ctx)}\n\n"
                f"It ranks #{patterns.index(p) + 1} of {len(patterns)} by unseen risk "
                f"(accumulated severity weighted by the fraction never reported)."
            )
            brief = ask(agent, prompt, PatternBrief)
            results.append((p, brief))

            if write:
                graph.run(
                    WRITE_BRIEF,
                    fp=p["fingerprint"],
                    title=brief.title,
                    hypothesis=brief.root_cause_hypothesis,
                    why_unreported=brief.why_unreported,
                    action=brief.recommended_action,
                    confidence=brief.confidence,
                )

        print("# Safety committee brief\n")
        print(f"Generated from {sum(p['occurrences'] for p in patterns)} camera-derived "
              f"events across {len(patterns)} recurring patterns.\n")

        for i, (p, b) in enumerate(results, 1):
            print(f"## {i}. {b.title}")
            print(f"*{p['occurrences']} events, {p['reports']} reported · "
                  f"confidence: {b.confidence}*\n")
            print(f"**Why it keeps happening.** {b.root_cause_hypothesis}\n")
            print(f"**Why nobody filed it.** {b.why_unreported}\n")
            print(f"**Do this week.** {b.recommended_action}\n")

        if write:
            print(f"\n(wrote titles and hypotheses onto {len(results)} Pattern nodes — "
                  f"src/demo.py will pick them up)")
    finally:
        graph.close()


if __name__ == "__main__":
    main()
