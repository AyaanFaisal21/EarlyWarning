# Demo run sheet

Five minutes. Four beats. Every number on screen comes from a live query — nothing is a
slide.

**Setup before you present:** `docker compose up -d && python src/ingest.py --reset`, Neo4j
browser open at <http://localhost:7474>, [queries.cypher](queries.cypher) pasted into a
scratch tab so you're never typing Cypher live.

---

## Beat 0 — the problem (35 seconds, no screen)

> Ninety percent of workplace near misses are never reported.
>
> Not because people are lazy — because nothing happened. The forklift stopped. The worker
> stepped back. There's nothing to file. You cannot fix a recognition failure with a better
> form.
>
> Meanwhile employers pay over a billion dollars a week in direct workers' comp.

**Then get ahead of the obvious objection immediately:**

> The usual answer is "count near misses." That was tried for ninety years and it failed —
> minor injuries fell for decades while fatalities didn't. So the industry moved to SIF
> potential: not how many, but which ones could have killed someone.
>
> That's a judgement about what you're looking at. Which is why it's still a human job.

⚠️ **Do not cite Heinrich's pyramid as fact.** It's discredited, and an EHS judge will know.
Cite it as the thing that failed — see [SAFETY_EVIDENCE.md](SAFETY_EVIDENCE.md) §3.

---

## Beat 1 — the inversion (45 seconds)

Run the ingest live, or show the output you already have:

```
could have killed someone:  54 events,  6% reported
minor potential:            55 events, 73% reported
```

> Same site, same twelve weeks. The events that could have killed somebody were reported six
> percent of the time. The trivial ones, seventy-three.
>
> Reporting doesn't fail randomly. It collapses exactly where severity climbs.

---

## Beat 2 — frequency is the wrong ranking (60 seconds)

Run **Q0**, both halves. Rank by count, then by SIF potential.

Point at slip/trip: **second most frequent hazard in the building, and it does not appear in
the fatal-potential list at all.**

Then run **Q2** and point at the bottom row:

```
forklift — vehicle pedestrian proximity, no segregated walkway   42 occ    6 rep   133.7
overhead crane — suspended load, no exclusion zone               18 occ    0 rep   108.0
delivery vehicle — vehicle pedestrian proximity, no walkway        6 occ    0 rep    32.0
scissor lift — working at height, no fall arrest                   4 occ    3 rep     8.0
pedestrian worker — slip trip hazard, no floor marking            39 occ   34 rep     6.7
```

> Slip-trip is the second most common thing that happens here and the least important thing
> on this list — because it's minor and everyone already knows about it. The crane, eighteen
> events, zero reports, is invisible.
>
> This is the ranking that replaces counting.

---

## Beat 3 — normalization of deviance, computed (75 seconds) ← the close

Set up with the concept first, in one sentence:

> Diane Vaughan named this studying Challenger. Normalization of deviance: a practice drifts
> until it stops feeling wrong. O-ring blow-by was *accepted as a risk*. So were foam
> strikes, before Columbia.

Run **Q3**:

```
forklift — vehicle pedestrian proximity, no segregated walkway
  before: 23 events   proximity 1.83   26% reported
  now:    19 events   proximity 0.74    0% reported
```

> Same hazard, same site. Six weeks ago it was one-to-three metres and a quarter of them got
> written up. Now it's under a metre — some of it contact — and **not one has been reported.**
>
> Nobody decided to stop reporting. It stopped feeling like an event.

**The line to end on:**

> Normalization of deviance is a memory failure. It happens because nobody compares today
> against two years ago. Each event, on its own, looks survivable — because each one *was*
> survivable, until one wasn't.
>
> No human holds that comparison across four thousand hours of footage. A graph does.

---

## Beat 4 — the action (25 seconds)

Run **Q4**. End on something someone can go and do:

```
segregated_walkway   32 high-potential events   across 2 distinct patterns
```

> One control. Thirty-two events that could have killed someone, across two different
> situations nobody had connected. That's a work order, not a dashboard.

---

## If there's time: the agent

```bash
python src/agent.py "which patterns are getting worse and why?"
```

Worth showing that it calls `get_graph_schema` before writing Cypher — that's the difference
between a working demo and one that hallucinates node labels you never created.

---

## Questions you will get

**"Isn't this Voxel AI / viAct?"** — Name them before the judge does. They do near-miss
*detection*. This is a **reporting-gap audit**: what the cameras saw, minus what the log
recorded. Different output, and it's the delta that has value.

**"Isn't this just surveillance?"** — The unit of analysis is the hazard, never the person.
No identification, no re-identification, no worker-level metrics. Say it before you're asked.

**"How do you know the SIF ratings are right?"** — We don't, and we don't claim to. It ranks
a review queue; a human closes the loop. The alternative today is nobody looking at all.

**"Is the data real?"** — No, and say so plainly. It's synthetic and deliberately built to
contain a known drift signal so the queries can be checked against ground truth. No public
corpus of workplace near-miss footage exists — the footage that matters is the footage
nobody publishes, which is part of why the problem persists.

**"Why not just a vector database?"** — Every query here is absence, counting, or traversal.
Ask a vector index what's *missing* and it returns the closest thing that exists. That answer
is silently wrong, which is worse than no answer.
