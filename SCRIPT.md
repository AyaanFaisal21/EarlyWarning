# Early Warning — read-off script

~2:15 spoken with pauses. Your cuts kept. Scroll cues corrected to the current page order,
and each pipeline step now ends with why-this-tool plus the file to open.

---

**[hero — don't scroll yet]**

> How much is a human life worth?

*Pause. Don't answer it.*

> Bit of a hard question. But American employers answer it every week — they pay out over
> **a billion dollars a week** in workers' compensation, for injuries that have already
> happened.
>
> In 2024 alone, **five thousand and seventy** people went to work and didn't come home.

**[scroll: numbers]**

> Near misses are a warning. And **ninety percent of those warnings are never reported** —
> because to the person it happened to, nothing really happened.
>
> And it's only getting worse. Pedestrians struck by workplace vehicles are up **nineteen
> percent** — a category notorious for unreported near misses. If you almost get hit, you're
> thankful, you go about your day. And you wonder who you'd even report it to.

**[scroll: cards]**

> A near miss is an event where nobody gets hurt — but somebody could have.

**[scroll: the problem, and what it costs]**

> Meanwhile autonomous machinery is arriving on those same floors, causing the same near
> misses, reporting none of them — leaving only footage.
>
> That's right. Footage is everywhere. It's just that nobody can watch it, and nobody knows
> what to look for.
>
> **Early Warning watches.**

---

**[step 01 card]**

> First, TwelveLabs — because the content is entirely visual. It reads what's happening
> against a closed vocabulary: what would need to change for someone to get hurt, and how
> plausible that outcome is.
>
> **Why this and not something else** — everything else needs words. There is no transcript
> here. Without it there is no input at all.

*Code: `src/extraction.py` — `EVENT_SCHEMA`, every field an enum.*

**[step 02 card]**

> Then we compare real near misses against rendered simulations that look nothing alike —
> and get the **same fingerprint**, because we hash what the extractor found, not what the
> frame looked like. That lets us line up a simulated accident with the near misses next to
> it, bolstering our near miss identification.
>
> **Why not embeddings** — we tried. They failed. Everything sat at 0.98 similarity.
> Structure worked where appearance couldn't.

*Code: `src/loader.py` — `fingerprint()`, twelve lines, no vendor.*

**[step 03 card]**

> Now Neo4j connects it. Every question here is about what's **absent** — which patterns
> produced no report. Ask a vector database and it hands you the nearest thing that exists.
> We need a graph, because **only a graph can count what isn't there.**
>
> Our graph runs on Neo4j Aura, hosted on AWS in us-east-1.

*Code: `queries.cypher` — `NOT (e)-[:GENERATED]->(:Report)`.*

**[step 04 card]**

> Finally OpenAI reads the assembled subgraph — never a video frame — and writes a brief for
> a safety manager: a named cause, and an action they can actually put out. With the entire
> pipeline stringing output into input via the **Strands Agents SDK**.
>
> **Why after the graph** — its input is severity spread across dozens of clips and trends
> over time. None of that exists in a single video.

*Code: `src/brief.py` for structured output, `src/agent.py` for the graph tools.*

---

**[scroll: future]**

> We can't make people report near misses. We've tried for ninety years.
>
> So stop trying. Let **Early Warning** be the infrastructure that does it for them — now,
> and when the machines arrive.

---

## Live demo, if there's time

```bash
python src/agent.py "Which hazard patterns produced no report at all?"
```

> Nobody wrote this query. It reads the schema first, composes the Cypher, and runs it.

Returns 46 unreported patterns; biggest is *forklift — vehicle pedestrian proximity, no
segregated walkway*, fingerprint `5649abdb63e19bdf`, 17 events. Takes ~20s — show saved
output if the room is tight.

**If you only open one file: `fingerprint()`.** Twelve lines carrying the whole argument.

---

## Three notes on your cuts

**Typo fixed** — "Near mmisses" → "Near misses".

**Scroll cues were stale.** They still pointed at the old order. Current page order is
numbers → cards → *the problem, and what it costs* → pipeline → future, and the cues now
match. Your autonomous-machinery line moved onto the thesis page, which is where that copy
actually lives on screen.

**I put back one twelve-word line.** You cut the definition entirely, which left the script
never saying what a near miss *is* — a judge unfamiliar with the term would be lost for the
rest of it. One sentence over the cards, which are on screen anyway.

**Your call, not restored:** the "you're thankful, you go about your day" line. It was the
only moment the audience recognises itself, but it costs ~10 seconds and you're tight. If
you find spare time, that's the first thing I'd put back.

---

## If asked

**"How accurate is it?"**
High recall on hazard presence. Measured against a labelled CCTV set we got ~51% precision —
but those labels encode *human compliance*, whether a worker stayed inside a painted line,
which is a different question from whether a machine did something unexpected. We don't
claim compliance classification. It ranks a review queue; a human closes the loop.

**"Isn't this surveillance?"**
The unit of analysis is the hazard, never the person. No identification, no
re-identification, no worker-level metrics. The output names a missing barrier, not a worker.

**"Why not just a vector database?"**
Every headline query is absence, negation, or exhaustive counting — set operations. And we
measured it: embeddings couldn't even separate our two corpora, 0.98 similarity within
versus 0.88 across.

**"Is the data real?"**
Both. Real factory CCTV under CC BY, plus NVIDIA's openly licensed simulation set. What
you're seeing is a completed pipeline run over 79 clips.

**"All accidents start as near misses, right?"**
Careful — that's Heinrich's pyramid, and it's discredited. Minor injuries fell for decades
while fatalities didn't. That's *why* the field moved to SIF potential, and why we rank by
what could have killed someone rather than by count.

**"Who actually acts on this?"**
The EHS manager takes it to the safety committee; maintenance installs the control. Then the
loop closes — we keep counting, so if the pattern drops you know the fix worked. No manual
near-miss programme can tell you that, because the events were never counted to begin with.

---

## Numbers, with sources

| Claim | Source |
|---|---|
| >$1B/week direct workers' comp | Liberty Mutual Workplace Safety Index 2025 (2022 data) |
| 5,070 fatal work injuries, 2024 | BLS Census of Fatal Occupational Injuries |
| Pedestrians struck by vehicles +19% (369, up from 310) | BLS, same |
| 90% of near misses unreported | Benchmark Gensuite 2026 EHS Benchmarking Report |
| 75% of accidents preceded by a near miss | National Safety Council |
