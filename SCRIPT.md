# Early Warning — read-off script

Trimmed to ~2:05 spoken, ~2:15 with the pauses. Scroll cues in brackets.
Your wording, tightened — nothing here is a claim we can't defend.

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

> The National Safety Council says three quarters of workplace accidents were preceded by a
> near miss. A warning. And **ninety percent of those warnings are never reported** —
> because to the person it happened to, nothing really happened.
>
> That's what a near miss is. An event where nobody gets hurt, but one that often comes
> before an accident.

**[scroll: cards]**

> And it's getting worse. Pedestrians struck by workplace vehicles are up **nineteen
> percent** — a category notorious for unreported near misses. If you almost get hit,
> you're thankful, you go about your day. And you wonder who you'd even report it to.
>
> Meanwhile autonomous machinery is arriving on those same floors, causing the same near
> misses, reporting none of them — leaving only footage.

**[scroll: the problem, and what it costs]**

> That's right. Footage is everywhere. It's just that nobody can watch it, and nobody knows
> what to look for.
>
> **Early Warning watches.**

---

**[step 01 card]**

> First, TwelveLabs — because the content is entirely visual. It reads what's happening
> against a closed vocabulary: what would need to change for someone to get hurt, and how
> plausible that outcome is.

**[step 02 card]**

> Then we compare real near misses against rendered simulations that look nothing alike —
> and get the **same fingerprint**, because we hash what the extractor found, not what the
> frame looked like. That lets us line up a simulated accident with the near misses next to
> it.

**[step 03 card]**

> Now Neo4j connects it. Every question here is about what's **absent** — which patterns
> produced no report. Ask a vector database and it hands you the nearest thing that exists.
> We need a graph, because **only a graph can count what isn't there.**

**[step 04 card]**

> Finally OpenAI reads the assembled subgraph — never a video frame — and writes a brief for
> a safety manager: a named cause, and an action they can actually put out.

---

**[scroll: future]**

> We can't make people report near misses. We've tried for ninety years.
>
> So stop trying. Let **Early Warning** be the infrastructure that does it for them — now,
> and when the machines arrive.

---

## What changed from your draft

| | |
|---|---|
| **−22 words** | Kept one side of the "you're thankful" line. The second half already carries both perspectives |
| **−15** | Neo4j paragraph: one example question instead of two, and your missing clause filled in |
| **−12** | Autonomous machinery compressed into one sentence, which also cleans the pivot |
| **−10** | Close trimmed — it was doing two jobs |
| **−4** | Dropped "warehouse and workplace" from the money line; unqualified is stronger |
| **wording** | *"usually precedes an accident"* → *"often comes before one."* The strong version is Heinrich's causal chain, which is discredited — this is the one line an EHS-literate judge could push on |

**Protected deliberately:** the "you're thankful, you go about your day" line — it explains
non-reporting better than the 90% figure does, and it's the only moment the audience
recognises themselves. And "Footage is everywhere… Early Warning watches" — 20 words doing
the entire problem-to-product pivot.

---

## If you're still long

Cut the step 02 paragraph entirely (−45 words, ~18s). The fingerprint story is the most
technically impressive thing you have, but it's the only section the argument survives
without.

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
