# Early Warning — 2 minute script

Roughly 300 words spoken. Scroll cues in brackets. Every number is sourced and every
claim is one we can defend if challenged.

---

### 0:00 — the problem  *[hero, then scroll to thesis]*

> A near miss is an event where nobody got hurt — but somebody could have.
>
> They're almost never reported. Not because people are careless, but because **nothing
> happened.** The forklift stopped. The worker stepped back. There's nothing to file.
>
> Ninety percent go unreported. And the National Safety Council says three quarters of
> accidents were preceded by at least one.

*Beat.*

> So the warning exists. It just never reaches anyone.

---

### 0:30 — why it's getting worse  *[scroll to numbers]*

> Workplace deaths in the US fell four percent last year. But **pedestrians struck by
> vehicles at work rose nineteen percent.** The category that's getting worse is exactly
> the one nobody files reports about.
>
> And autonomous machinery is arriving on those same floors. It'll cause near misses too,
> and it won't report them either.
>
> **At best, it records them.** Which is the opening — that footage already exists, and
> nobody has the hours to watch it.

---

### 1:00 — what we built  *[scroll to pipeline]*

> Early Warning reads the recordings nobody opens.
>
> **TwelveLabs watches** — the signal here is entirely visual, there's no transcript to
> fall back on. We constrain it to a closed vocabulary: hazard type, which safety control
> was missing, and what would have had to change for someone to get hurt.

*[step 02 card]*

> **Then the part I'd point at.** On the left, real factory CCTV. On the right, a rendered
> simulation from another continent. They look nothing alike — and they produce the
> **same fingerprint**, because we hash what the extractor found, not what the frame
> looked like.
>
> We tried matching them on embeddings first. It failed — everything sat at 0.98
> similarity. Structure worked where appearance didn't.
>
> And the simulations do something else for us. Our extractor writes down what *would* have
> had to change for someone to get hurt. The simulation set shows that same configuration
> with less margin left — **the counterfactual, rendered.** One of them has a person seated
> on the forks of a moving forklift. Same hazard, no margin.

*[step 03 card]*

> **Neo4j connects it**, and this is why it has to be a graph. Every question here is
> about what's *absent*. Which patterns produced no report. Which missing control spans
> the most events. Ask a vector database what's missing and it hands you the nearest thing
> that exists — confidently wrong.

---

### 1:40 — the outcome

> **OpenAI reads the assembled subgraph** — never a video frame — and writes a brief a
> safety manager acts on. Named cause, and one action they can verify by Friday.
>
> And then the loop closes: we keep counting. If the pattern drops, the fix worked. **No
> manual near-miss programme can tell you that**, because the events were never counted in
> the first place.

---

### 2:00 — close  *[scroll to future]*

> We can't make people report near misses. We've tried for ninety years.
>
> So don't. Take the burden off them entirely — the cameras are already up there.

---

## If asked

**"How accurate is it?"**
High recall on hazard presence. We measured it against a labelled CCTV set and got ~51%
precision — but those labels encode *human compliance*, whether a worker stayed inside a
painted line, which is a different question from whether a machine did something
unexpected. We're not claiming compliance classification. It ranks a review queue; a human
closes the loop.

**"Isn't this surveillance?"**
The unit of analysis is the hazard, never the person. No identification, no
re-identification, no worker-level metrics. The output names a missing barrier, not a
worker.

**"Why not just a vector database?"**
Every headline query is absence, negation, or exhaustive counting. Those are set
operations. We have the measurement: embeddings couldn't even separate our two corpora.

**"Is the data real?"**
Both. Real factory CCTV under CC BY, plus NVIDIA's openly licensed simulation set. The
graph you're looking at is a completed pipeline run over 79 clips.

**"What about Heinrich's pyramid / all accidents start as near misses?"**
Don't use it and don't accept it. It's discredited — minor injuries fell for decades while
fatalities didn't. That's *why* the field moved to SIF potential, and why we rank by what
could have killed someone rather than by count.
