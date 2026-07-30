# Early Warning — 2 minute script

~320 words spoken. Scroll cues in brackets. Every number is sourced; every claim survives
being challenged. Read it aloud once against a live scroll before you present.

---

### 0:00 — the grabber  *[hero, don't scroll yet]*

> **How much is a human life worth?**

*Let that sit for a beat. Don't answer it.*

> American employers answer it every week. They pay out **over a billion dollars a week**
> in workers' compensation — for injuries that have already happened.
>
> Last year, **five thousand and seventy** people went to work and didn't come home.
>
> The National Safety Council says three quarters of workplace accidents were preceded by a
> near miss. A warning. And **ninety percent of those warnings are never reported by
> anyone.**

*Beat.*

> So what actually is a near miss, in a warehouse?

---

### 0:30 — the answer  *[scroll: thesis → cards]*

> An event where nobody got hurt — but somebody could have. The forklift stopped. The
> worker stepped back. The load swung past.
>
> **Nothing happened. Which is exactly why nothing gets filed.** You can't blame someone
> for not reporting an event they didn't recognise as an event.
>
> And it's getting worse. Workplace deaths fell four percent last year — but **pedestrians
> struck by vehicles at work rose nineteen percent.** The category getting worse is the one
> nobody reports.
>
> Autonomous machinery is arriving on those same floors. It'll cause near misses too, and
> it won't report them either. **At best, it records them.**

---

### 1:00 — what we built  *[scroll to pipeline]*

> That footage already exists. Nobody has the hours to watch it. So we do.
>
> **TwelveLabs watches.** The signal is entirely visual — there's no transcript here. We
> constrain it to a closed vocabulary: the hazard, which safety control was missing, and
> what would have had to change for someone to get hurt.

*[step 02 card]*

> **This is the part I'd point at.** Left, real factory CCTV. Right, a rendered simulation
> from another continent. They look nothing alike — and they produce the **same
> fingerprint**, because we hash what the extractor found, not what the frame looked like.
>
> We tried matching them on embeddings first. It failed — everything sat at 0.98 similarity.
> Structure worked where appearance didn't.

*[step 03 card]*

> **Neo4j connects it** — and this is why it has to be a graph. Every question here is about
> what's *absent*. Which patterns produced no report. Which missing control spans the most
> events. Ask a vector database what's missing and it hands you the nearest thing that
> exists. Confidently wrong.

---

### 1:40 — the outcome

> **OpenAI reads the assembled subgraph** — never a video frame — and writes a brief a
> safety manager acts on. Named cause, one action they can verify by Friday.
>
> Then the loop closes: we keep counting. If the pattern drops, the fix worked. **No manual
> near-miss programme can tell you that**, because the events were never counted to begin
> with.

---

### 2:00 — close  *[scroll to future]*

> We can't make people report near misses. We've tried for ninety years.
>
> So stop trying. Take the burden off them entirely — the cameras are already up there.

---

## Cuts, if you're running long

Drop the embeddings sentence at 1:20 and the counterfactual aside. Keeps the spine intact.

## Optional aside — the contact clip

If you want one more beat on step 02: *"One clip in the set has a person seated on the
forks of a moving forklift. Same hazard, no margin."* Only say it if you have time; it's
colour, not argument.

---

## If asked

**"How accurate is it?"**
High recall on hazard presence. We measured against a labelled CCTV set and got ~51%
precision — but those labels encode *human compliance*, whether a worker stayed inside a
painted line, which is a different question from whether a machine did something
unexpected. We don't claim compliance classification. It ranks a review queue; a human
closes the loop.

**"Isn't this surveillance?"**
The unit of analysis is the hazard, never the person. No identification, no
re-identification, no worker-level metrics. The output names a missing barrier, not a
worker.

**"Why not just a vector database?"**
Every headline query is absence, negation, or exhaustive counting — set operations. And we
have the measurement: embeddings couldn't even separate our two corpora.

**"Is the data real?"**
Both. Real factory CCTV under CC BY, plus NVIDIA's openly licensed simulation set. What
you're looking at is a completed pipeline run over 79 clips.

**"All accidents start as near misses, right?"**
Careful — that's Heinrich's pyramid, and it's discredited. Minor injuries fell for decades
while fatalities didn't. That's *why* the field moved to SIF potential, and why we rank by
what could have killed someone rather than by count.

---

## Numbers, with sources

| Claim | Source |
|---|---|
| >$1B/week direct workers' comp | Liberty Mutual Workplace Safety Index 2025 (2022 data) |
| 5,070 fatal work injuries, 2024 | BLS Census of Fatal Occupational Injuries |
| Pedestrians struck by vehicles +19% (369, up from 310) | BLS, same |
| 90% of near misses unreported | Benchmark Gensuite 2026 EHS Benchmarking Report |
| 75% of accidents preceded by a near miss | National Safety Council |
| Deaths down 4% year on year | BLS, same |
